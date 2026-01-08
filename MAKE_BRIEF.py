# -*- coding: utf-8 -*-
import logging
import sqlite3
from datetime import datetime, timedelta
import asyncio
from typing import Union
from telegram import Update, ReactionTypeEmoji
from telegram.helpers import escape_markdown
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ChatMemberHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ChatMemberStatus
from telegram.error import TelegramError, BadRequest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- ⚙️ 설정 ---
TELEGRAM_BOT_TOKEN = "-----------" # 실제 토큰으로 변경하세요
ADMIN_GROUP_ID = "---------" # 실제 관리자 그룹 ID로 변경하세요
CHANNELS = {
    # --- 자동 추방 기능이 필요한 채널 ---
    "-1002930721999": {"name": "🌸VIP Crypto KK🔥🌸 2기", "kick_enabled": True, "default_days": 7},
    "-1003081779651": {"name": "VIP 검정개미 아카데미 2기", "kick_enabled": True, "default_days": 7},
    "-1003050352036": {"name": "VIP 주식 비스트로 2기", "kick_enabled": True, "default_days": 7},
    "-1003098990495": {"name": "코인1번가 2기" , "kick_enabled": True, "default_days": 7},

    # --- 입장/퇴장 로그만 필요한 채널 ---
    "-1002766472889": {"name": "시크릿 코인 2기", "kick_enabled": False},
    "-1003176222791": {"name": "검정개미 아카데미 2기", "kick_enabled": False},
    "-1002950756040": {"name": "🌸Crypto KK🔥🌸 2기", "kick_enabled": False},
    "-1002930074726": {"name": "주식 비스트로 2기", "kick_enabled": False},
    "-1003035045830": {"name": "골드코인 2기" , "kick_enabled": False},
}

ALL_CHANNEL_IDS = [int(id) for id in CHANNELS.keys()]
KICK_ENABLED_CHANNEL_IDS = [int(id) for id, props in CHANNELS.items() if props["kick_enabled"]]

# --- 로깅 설정 ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 데이터베이스 설정 ---
DB_FILE = "members.db"
MAX_DAYS_ALLOWED = 36500

def setup_database():
    conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            user_id INTEGER NOT NULL, channel_id INTEGER NOT NULL, user_name TEXT,
            kick_timestamp INTEGER NOT NULL, log_message_id INTEGER,
            PRIMARY KEY (user_id, channel_id)
        )
    """)
    conn.commit(); conn.close(); logger.info("데이터베이스가 준비되었습니다.")

# --- 데이터베이스 함수 ---
def add_new_user(user_id, user_name, channel_id, days=7, log_message_id=None):
    days_safe = min(days, MAX_DAYS_ALLOWED)
    try: kick_time = datetime.now() + timedelta(days=days_safe)
    except OverflowError: kick_time = datetime.max
    kick_timestamp = int(kick_time.timestamp())
    conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
    safe_user_name = user_name if user_name is not None else ""
    cursor.execute("INSERT OR REPLACE INTO members (user_id, user_name, channel_id, kick_timestamp, log_message_id) VALUES (?, ?, ?, ?, ?)",
                   (user_id, safe_user_name, channel_id, kick_timestamp, log_message_id)); conn.commit(); conn.close()

def set_user_expiry(user_id, channel_id, days_to_set):
    days_to_set_safe = min(days_to_set, MAX_DAYS_ALLOWED)
    try: kick_time = datetime.now() + timedelta(days=days_to_set_safe)
    except OverflowError: kick_time = datetime.max
    new_kick_timestamp = int(kick_time.timestamp())
    conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
    cursor.execute("UPDATE members SET kick_timestamp = ? WHERE user_id = ? AND channel_id = ?", (new_kick_timestamp, user_id, channel_id)); conn.commit(); conn.close()
    return days_to_set_safe, kick_time

def extend_user_expiry(user_id, channel_id, days_to_add):
    conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT kick_timestamp FROM members WHERE user_id = ? AND channel_id = ?", (user_id, channel_id))
    result = cursor.fetchone(); current_timestamp = int(datetime.now().timestamp())
    days_to_add_safe = min(days_to_add, MAX_DAYS_ALLOWED)
    base_time = datetime.fromtimestamp(result[0]) if result and result[0] > current_timestamp else datetime.now()
    try: new_kick_time = base_time + timedelta(days=days_to_add_safe)
    except OverflowError: new_kick_time = datetime.max
    new_kick_timestamp = int(new_kick_time.timestamp())
    cursor.execute("UPDATE members SET kick_timestamp = ? WHERE user_id = ? AND channel_id = ?", (new_kick_timestamp, user_id, channel_id)); conn.commit(); conn.close()
    return days_to_add_safe, new_kick_time

def get_user_info(user_id, channel_id):
    conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT user_name, log_message_id FROM members WHERE user_id = ? AND channel_id = ?", (user_id, channel_id))
    result = cursor.fetchone(); conn.close(); return result if result else (None, None)
def remove_user(user_id, channel_id):
    conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
    cursor.execute("DELETE FROM members WHERE user_id = ? AND channel_id = ?", (user_id, channel_id)); conn.commit(); conn.close()

# --- Helper Function to Send Message with Fallback ---
async def send_admin_message(context: Union[ContextTypes.DEFAULT_TYPE, Application], text: str, parse_mode: Union[str, None] = 'Markdown') -> Union[Update.MESSAGE, None]:
    if isinstance(context, Application): bot = context.bot
    elif hasattr(context, 'bot'): bot = context.bot
    else: logger.error(f"send_admin_message에 예상치 못한 타입({type(context)}) 전달됨"); return None

    sent_message = None
    try:
        sent_message = await bot.send_message(chat_id=ADMIN_GROUP_ID, text=text, parse_mode=parse_mode)
    except BadRequest as e:
        if "Can't parse entities" in str(e):
            logger.warning(f"Markdown 전송 실패 ({e}), Plain text로 재시도...")
            try: sent_message = await bot.send_message(chat_id=ADMIN_GROUP_ID, text=text)
            except Exception as e2: logger.error(f"Plain text 알림 재전송 실패: {e2}")
        else: logger.error(f"관리자 그룹 메시지 전송 실패 (BadRequest): {e}")
    except Exception as e: logger.error(f"관리자 그룹 메시지 전송 중 예상치 못한 오류: {e}")
    return sent_message

# --- 텔레그램 봇 핸들러 ---

async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = update.chat_member
    if (not result or
            result.chat.id not in ALL_CHANNEL_IDS or
            (result.from_user and result.from_user.id == context.bot.id)):
        return

    user = result.new_chat_member.user; channel_id = result.chat.id
    channel_props = CHANNELS.get(str(channel_id))
    if not channel_props: return

    channel_name = channel_props["name"]
    is_kick_enabled = channel_props["kick_enabled"]
    user_name = user.full_name if user.full_name else "이름없음"

    # --- 새 멤버 입장 ---
    if (result.new_chat_member.status == ChatMemberStatus.MEMBER and
        result.old_chat_member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED, "kicked")):

        log_message_text = ""
        if is_kick_enabled:
            default_days = channel_props.get("default_days", 7)
            log_message_text = (
                f"🔔 {channel_name} 신규 회원 입장\n\n"
                f"**이름:** {user_name}\n"
                f"**ID:** `{user.id}`\n"
                f"**만료:** {default_days}일 뒤\n\n"
                f"👇 아래 명령어로 기간을 관리하세요.\n"
                f"1️⃣ `{'/set'} {user.id} 30 {channel_name}`\n"
                f"2️⃣ `{'/add'} {user.id} 30 {channel_name}`"
            )
        else:
            log_message_text = (
                f"🟢 {channel_name} 회원 입장\n\n"
                f"**이름:** {user_name}\n"
                f"**ID:** `{user.id}`"
            )

        sent_message = await send_admin_message(context, log_message_text)

        if sent_message and is_kick_enabled:
            await asyncio.to_thread(add_new_user, user.id, user.full_name, channel_id, days=default_days, log_message_id=sent_message.message_id)

    # --- 멤버 스스로 퇴장 ---
    elif (result.new_chat_member.status == ChatMemberStatus.LEFT and
          result.old_chat_member.status == ChatMemberStatus.MEMBER):
        if is_kick_enabled: await asyncio.to_thread(remove_user, user.id, channel_id)

        log_message_text = (
            f"🔴 {channel_name} 회원 퇴장\n\n"
            f"**이름:** {user_name}\n"
            f"**ID:** `{user.id}` (스스로 나감)"
        )
        await send_admin_message(context, log_message_text)

    # --- 관리자에 의해 추방됨 ---
    elif (result.new_chat_member.status in (ChatMemberStatus.BANNED, "kicked") and
          result.old_chat_member.status == ChatMemberStatus.MEMBER):
        if is_kick_enabled: await asyncio.to_thread(remove_user, user.id, channel_id)

        admin_name = result.from_user.full_name if result.from_user and result.from_user.id != user.id else ""
        admin_info = f" (수행자: {admin_name})" if admin_name else ""
        log_message_text = (f"🔨 {channel_name} 관리자 추방\n\n" f"**대상:** {user_name} (`{user.id}`){admin_info}")

        await send_admin_message(context, log_message_text)

async def auto_reaction_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update.channel_post: await update.channel_post.set_reaction(reaction=ReactionTypeEmoji("👍"))
    except Exception as e: logger.error(f"자동 호응 기능 처리 중 오류 발생: {e}")

# [수정됨] is_admin 함수 삭제됨

async def command_parser(update: Update, context: ContextTypes.DEFAULT_TYPE, command_func, command_name):
    # [수정됨] 관리자 그룹인지 확인하는 로직만 유지, is_admin() 체크 제거
    if update.effective_chat.id != int(ADMIN_GROUP_ID): return
    
    # [수정됨] is_admin 확인 제거 -> 무조건 실행

    try:
        if len(context.args) < 3: raise ValueError("인수가 부족합니다.")

        user_id = int(context.args[0])
        days_input = int(context.args[1])
        channel_name_arg = " ".join(context.args[2:])

        target_channel_id, original_channel_name = None, None
        for cid, cprops in CHANNELS.items():
            if cprops['name'] == channel_name_arg:
                target_channel_id, original_channel_name = int(cid), cprops['name']
                break

        if not target_channel_id:
            await update.message.reply_text(f"'{channel_name_arg}' 채널을 찾을 수 없습니다."); return

        days_applied, new_expiry_date = await asyncio.to_thread(command_func, user_id, target_channel_id, days_input)
        user_name, log_message_id = await asyncio.to_thread(get_user_info, user_id, target_channel_id)

        user_name_display = user_name if user_name else "정보없음"
        admin_name_display = update.effective_user.full_name if update.effective_user.full_name else ""

        feedback_text = ""
        if command_name == 'set':
            feedback_text = (
                f"✅ {original_channel_name} 기간 **설정** 완료\n\n"
                f"**대상:** {user_name_display} (`{user_id}`)\n"
                f"**적용 기간:** {days_applied}일 " + (f"(입력: {days_input}일)" if days_applied != days_input else "") + "\n"
                f"**새 만료일:** {new_expiry_date.strftime('%Y년 %m월 %d일')}로 설정\n"
                f"(수정자: {admin_name_display})"
            )
        else: # add
            feedback_text = (
                f"✅ {original_channel_name} 기간 **연장** 완료\n\n"
                f"**대상:** {user_name_display} (`{user_id}`)\n"
                f"**누적 연장:** {days_applied}일 추가 " + (f"(입력: {days_input}일)" if days_applied != days_input else "") + "\n"
                f"**새 만료일:** {new_expiry_date.strftime('%Y년 %m월 %d일')}\n"
                f"(수정자: {admin_name_display})"
            )

        feedback_text += (
            f"\n\n👇 아래 명령어로 기간을 관리하세요.\n"
            f"1️⃣ `{'/set'} {user_id} 30 {original_channel_name}`\n"
            f"2️⃣ `{'/add'} {user_id} 30 {original_channel_name}`"
        )

        sent_feedback = await send_admin_message(context, feedback_text)

        if log_message_id and sent_feedback:
            try: await context.bot.edit_message_text(chat_id=ADMIN_GROUP_ID, message_id=log_message_id, text=feedback_text, parse_mode='Markdown')
            except BadRequest as e:
                 if "Can't parse entities" in str(e):
                    logger.warning(f"로그 메시지 ID {log_message_id} 수정 실패 (Markdown 오류), Plain text 재시도...")
                    try: await context.bot.edit_message_text(chat_id=ADMIN_GROUP_ID, message_id=log_message_id, text=feedback_text)
                    except Exception as e_edit_plain: logger.error(f"Plain text 로그 수정 실패: {e_edit_plain}")
                 else: logger.warning(f"로그 메시지 ID {log_message_id} 수정 실패: {e}")
            except Exception as e_edit: logger.warning(f"로그 메시지 ID {log_message_id} 수정 중 예상치 못한 오류: {e_edit}")

    except (ValueError, IndexError):
        await update.message.reply_text(f"명령어 형식 오류. 예:\n`/{command_name} 12345 30 \"{list(CHANNELS.values())[0]['name']}\"`", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"/{command_name} 명령어 처리 중 오류: {e}", exc_info=True)
        await send_admin_message(context, f"명령어 처리 중 오류 발생: {escape_markdown(str(e), version=2)}", parse_mode='MarkdownV2')

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await command_parser(update, context, set_user_expiry, 'set')
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await command_parser(update, context, extend_user_expiry, 'add')

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # [수정됨] 관리자 그룹인지 확인하는 로직만 유지, is_admin() 체크 제거
    if update.effective_chat.id != int(ADMIN_GROUP_ID): return
    
    # [수정됨] is_admin 확인 제거 -> 무조건 실행

    try:
        if not context.args: await update.message.reply_text("사용법: `/ban [사용자ID]`"); return

        user_id_to_ban = int(context.args[0])
        admin_name_display = update.effective_user.full_name if update.effective_user.full_name else ""
        success_channels, failed_channels = [], []

        for channel_id_str, props in CHANNELS.items():
            channel_id, channel_name = int(channel_id_str), props['name']
            try:
                await context.bot.ban_chat_member(chat_id=channel_id, user_id=user_id_to_ban)
                if props['kick_enabled']: await asyncio.to_thread(remove_user, user_id_to_ban, channel_id)
                success_channels.append(channel_name)
            except TelegramError as e: failed_channels.append(f"{channel_name} (사유: {e.message})")
            except Exception as e: failed_channels.append(f"{channel_name} (사유: {str(e)})")

        feedback_text = (
            f"--- 🔨 사용자 전체 채널 추방 실행 ---\n\n"
            f"대상 ID: {user_id_to_ban}\n"
            f"실행자: {admin_name_display}\n\n"
        )
        if success_channels: feedback_text += "✅ 성공:\n" + "\n".join([f"- {name}" for name in success_channels])
        if failed_channels: feedback_text += "\n\n❌ 실패:\n" + "\n".join([f"- {name}" for name in failed_channels])

        # Plain Text로 직접 전송
        await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=feedback_text)

    except (ValueError, IndexError): await update.message.reply_text("명령어 형식 오류. 예: `/ban 12345678`")
    except Exception as e:
        logger.error(f"/ban 명령어 처리 중 오류: {e}", exc_info=True)
        await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=f"/ban 명령어 처리 중 오류 발생: {e}") # Plain Text 오류 메시지

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # [수정됨] 관리자 그룹인지 확인하는 로직만 유지, is_admin() 체크 제거
    if update.effective_chat.id != int(ADMIN_GROUP_ID): return
    
    # [수정됨] is_admin 확인 제거 -> 무조건 실행

    try:
        if not context.args: await update.message.reply_text("사용법: `/unban [사용자ID]`"); return

        user_id_to_unban = int(context.args[0])
        admin_name_display = update.effective_user.full_name if update.effective_user.full_name else ""
        success_channels, failed_channels = [], []

        for channel_id_str, props in CHANNELS.items():
            channel_id, channel_name = int(channel_id_str), props['name']
            try:
                await context.bot.unban_chat_member(chat_id=channel_id, user_id=user_id_to_unban, only_if_banned=True)
                success_channels.append(channel_name)
            except TelegramError as e: failed_channels.append(f"{channel_name} (사유: {e.message})")
            except Exception as e: failed_channels.append(f"{channel_name} (사유: {str(e)})")

        feedback_text = (
            f"--- 🔓 사용자 전체 채널 차단 해제 실행 ---\n\n"
            f"대상 ID: {user_id_to_unban}\n"
            f"실행자: {admin_name_display}\n\n"
        )
        if success_channels: feedback_text += "✅ 성공:\n" + "\n".join([f"- {name}" for name in success_channels])
        if failed_channels: feedback_text += "\n\n❌ 실패:\n" + "\n".join([f"- {name}" for name in failed_channels])

        # Plain Text로 직접 전송
        await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=feedback_text)

    except (ValueError, IndexError): await update.message.reply_text("명령어 형식 오류. 예: `/unban 12345678`")
    except Exception as e:
        logger.error(f"/unban 명령어 처리 중 오류: {e}", exc_info=True)
        await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=f"/unban 명령어 처리 중 오류 발생: {e}") # Plain Text 오류 메시지


# --- 스케줄링 작업 ---
def get_expired_users_from_db():
    conn = sqlite3.connect(DB_FILE); cursor = conn.cursor(); expired_users = []
    try:
        cursor.execute("SELECT user_id, user_name, channel_id FROM members WHERE kick_timestamp < ?", (int(datetime.now().timestamp()),))
        expired_users = cursor.fetchall()
    except Exception as e: logger.error(f"만료된 멤버 조회 중 DB 오류: {e}")
    finally: conn.close()
    return expired_users

async def kick_expired_members(application: Application):
    logger.info("만료된 멤버 확인 작업을 시작합니다...")
    try: expired_users = await asyncio.to_thread(get_expired_users_from_db)
    except Exception as e: logger.error(f"get_expired_users_from_db 스레드 실행 중 오류: {e}"); return

    if not expired_users: logger.info("만료된 멤버가 없습니다."); return
    logger.info(f"{len(expired_users)}명의 만료된 멤버를 처리합니다.")

    for user_id, user_name, channel_id in expired_users:
        channel_name = CHANNELS.get(str(channel_id), {}).get("name", f"ID {channel_id}")
        user_name_display = user_name if user_name else "정보없음"
        try:
            await application.bot.ban_chat_member(chat_id=channel_id, user_id=user_id)
            logger.info(f"[{channel_name}] 사용자 {user_name_display}({user_id})가 만료되어 추방되었습니다.")
            kick_notification_text = (
                f"❌ {channel_name} 멤버십 만료\n\n"
                f"**대상:** {user_name_display} (`{user_id}`)\n"
                f"채널에서 자동 추방 처리되었습니다."
            )
            await send_admin_message(application, kick_notification_text)
        except TelegramError as e:
            if "user not found" in e.message.lower() or "member was not found" in e.message.lower(): logger.warning(f"[{channel_name}] {user_id} 추방 시도, 이미 채널에 없음.")
            elif "not enough rights" in e.message.lower() or "bot is not a member" in e.message.lower(): logger.error(f"[{channel_name}] 봇 권한 부족 또는 멤버가 아니라서 {user_id} 추방 불가: {e}")
            else: logger.error(f"[{channel_name}] {user_id} 처리 중 텔레그램 오류: {e}")
        except Exception as e: logger.error(f"[{channel_name}] {user_id} 처리 중 알 수 없는 오류: {e}", exc_info=True)
        finally: await asyncio.to_thread(remove_user, user_id, channel_id)

    logger.info("만료된 멤버 확인 작업을 완료했습니다.")

# --- 메인 실행 함수 ---
def main() -> None:
    setup_database()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(CommandHandler("set", set_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(MessageHandler(filters.Chat(chat_id=ALL_CHANNEL_IDS) & filters.ChatType.CHANNEL, auto_reaction_handler))

    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
    scheduler.add_job(kick_expired_members, "interval", hours=1, args=[application])

    async def post_init(app: Application):
        scheduler.start()
        logger.info("스케줄러가 시작되었습니다.")
    application.post_init = post_init

    logger.info("봇이 성공적으로 시작되었습니다. 폴링 대기 중...")

    allowed_updates = [Update.CHAT_MEMBER, Update.MESSAGE, Update.CHANNEL_POST]
    application.run_polling(allowed_updates=allowed_updates, poll_interval=1.0, timeout=10)

    if scheduler.running: scheduler.shutdown()
    logger.info("봇이 종료됩니다.")

if __name__ == "__main__":
    bot_token_placeholder = "봇 토큰"
    admin_group_placeholder = "YOUR_ADMIN_GROUP_ID_HERE"

    valid_token = TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN.strip() != bot_token_placeholder
    valid_admin_id = ADMIN_GROUP_ID and ADMIN_GROUP_ID != admin_group_placeholder and ADMIN_GROUP_ID.lstrip('-').isdigit()

    if not valid_token or not valid_admin_id:
        logger.critical("="*50)
        if not valid_token: logger.critical(" 오류: TELEGRAM_BOT_TOKEN이 설정되지 않았거나 기본값입니다.")
        if not valid_admin_id: logger.critical(" 오류: ADMIN_GROUP_ID가 설정되지 않았거나 유효한 ID 형식이 아닙니다 ('-100...' 형태 숫자).")
        logger.critical(" 코드 상단의 설정값을 실제 값으로 수정해주세요.")
        logger.critical("="*50)
    else:
        try: main()
        except Exception as e: logger.critical(f"봇 실행 중 최상위 레벨 오류 발생: {e}", exc_info=True)