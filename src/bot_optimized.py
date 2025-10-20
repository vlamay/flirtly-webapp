# src/bot_optimized.py - Optimized bot with database utilities

import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from src.database import init_db
from src.db_utils import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "8430527446:AAFLoCZqvreDpsgz4d5z4J5LXMLC42B9ex0"
WEBAPP_URL = "https://vlamay.github.io/flirtly-webapp/"

# Initialize
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Main keyboard with Web App"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚡ Открыть Flirtly",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="💕 Матчи", callback_data="matches")
        ],
        [
            InlineKeyboardButton(text="🎁 Пригласить", callback_data="referral"),
            InlineKeyboardButton(text="⭐ Premium", callback_data="premium")
        ]
    ])


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command with referral handling and user management"""
    telegram_id = message.from_user.id
    username = message.from_user.username
    
    # Get or create user
    user = await DatabaseManager.get_or_create_user(telegram_id, username)
    
    # Handle referral
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_telegram_id = int(args[1].replace("ref_", ""))
            result = await DatabaseManager.process_referral(referrer_telegram_id, user.id)
            
            if result['success']:
                # Notify referrer
                try:
                    await bot.send_message(
                        referrer_telegram_id,
                        f"🎁 <b>Новый реферал!</b>\n\n"
                        f"@{username or 'пользователь'} зарегистрировался по твоей ссылке!\n\n"
                        f"Ты получил +{result['referrer_bonus']} лайков! ❤️",
                        parse_mode="HTML"
                    )
                except:
                    pass
                
                referral_bonus_text = f"\n\n🎁 <b>Бонус за друга:</b> +{result['new_user_bonus']} лайков!"
        except:
            referral_bonus_text = ""
    else:
        referral_bonus_text = ""
    
    # Check if profile is complete
    if not user.name or not user.photos:
        # New user - needs onboarding
        welcome_text = f"""
<b>Привет, {message.from_user.first_name}! 👋</b>

Добро пожаловать в <b>Flirtly</b> ⚡

Современный сервис знакомств прямо в Telegram!{referral_bonus_text}

<b>Что тебя ждет:</b>
• 💕 Умный подбор совпадений
• ⚡ Swipe как в популярных приложениях
• 💬 Instant чат с совпадениями
• 🎁 Бонусы за приглашения

<b>Нажми кнопку ниже чтобы создать профиль!</b>
        """.strip()
    else:
        # Existing user with profile
        stats = await DatabaseManager.get_user_stats(user.id)
        welcome_text = f"""
<b>С возвращением, {user.name}! 👋</b>

<b>Твоя статистика:</b>
• ❤️ Лайков осталось: {stats.get('daily_likes_remaining', 0)}
• 💕 Совпадений: {user.matches_count}
• 👀 Просмотров профиля: {user.views_count}
• 📊 Лайков на этой неделе: {stats.get('likes_this_week', 0)}{referral_bonus_text}

<b>Открой приложение и продолжай свайп!</b>
        """.strip()
    
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@dp.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    """Handle data from Web App with optimized database operations"""
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        telegram_id = message.from_user.id
        
        user = await DatabaseManager.get_user_by_telegram_id(telegram_id)
        if not user:
            user = await DatabaseManager.get_or_create_user(telegram_id, message.from_user.username)
        
        if action == 'register':
            # Handle registration with all profile data
            success = await DatabaseManager.update_user_profile(
                telegram_id,
                name=data.get('name'),
                age=data.get('age'),
                gender=data.get('gender'),
                looking_for=data.get('looking_for'),
                bio=data.get('bio', ''),
                photos=','.join(data.get('photos', [])),
                city=data.get('city'),
                country=data.get('country'),
                latitude=data.get('latitude'),
                longitude=data.get('longitude')
            )
            
            if success:
                await message.answer(
                    f"🎉 <b>Регистрация завершена!</b>\n\n"
                    f"Добро пожаловать, {data.get('name')}!\n\n"
                    f"📍 Местоположение: {data.get('city', 'Не указано')}\n\n"
                    f"Теперь можешь начать искать совпадения! ⚡",
                    parse_mode="HTML"
                )
            else:
                await message.answer("❌ Ошибка при создании профиля")
        
        elif action == 'like' or action == 'superlike':
            profile_id = data.get('profile_id')
            is_super_like = (action == 'superlike')
            
            # Check limits
            if user.daily_likes_remaining <= 0:
                await message.answer(
                    "😔 <b>Лимит лайков исчерпан!</b>\n\n"
                    "Получи Premium для безлимитных лайков!",
                    parse_mode="HTML"
                )
                return
            
            # Create like
            like = await DatabaseManager.create_like(
                user.id,
                profile_id,
                is_super_like
            )
            
            if like:
                # Check for mutual like (match)
                is_mutual = await DatabaseManager.check_mutual_like(user.id, profile_id)
                
                if is_mutual:
                    # Create match
                    match = await DatabaseManager.create_match(user.id, profile_id)
                    
                    if match:
                        # Get matched user info
                        matched_user = await DatabaseManager.get_user_by_telegram_id(profile_id)
                        
                        await message.answer(
                            f"🎉 <b>Это Match!</b>\n\n"
                            f"Вы понравились друг другу с {matched_user.name if matched_user else 'пользователем'}!\n\n"
                            f"Теперь можете начать общаться! 💬",
                            parse_mode="HTML"
                        )
                        
                        # Notify matched user
                        if matched_user:
                            try:
                                await bot.send_message(
                                    matched_user.telegram_id,
                                    f"🎉 <b>Новое совпадение!</b>\n\n"
                                    f"Вы понравились друг другу с {user.name}!\n\n"
                                    f"Открой Flirtly и начни общаться! 💬",
                                    parse_mode="HTML",
                                    reply_markup=get_main_keyboard()
                                )
                            except:
                                pass
                else:
                    emoji = "⭐" if is_super_like else "❤️"
                    await message.answer(f"{emoji} Лайк отправлен!")
            else:
                await message.answer("❌ Ошибка при отправке лайка")
        
        elif action == 'skip':
            profile_id = data.get('profile_id')
            await DatabaseManager.create_skip(user.id, profile_id)
            await message.answer("👎 Пропущено")
        
    except Exception as e:
        logger.error(f"Error handling webapp data: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка")


@dp.callback_query(F.data == "profile")
async def callback_profile(callback):
    """Show detailed profile information"""
    user = await DatabaseManager.get_user_by_telegram_id(callback.from_user.id)
    
    if not user or not user.name:
        await callback.answer("Сначала создай профиль!", show_alert=True)
        return
    
    stats = await DatabaseManager.get_user_stats(user.id)
    
    profile_text = f"""
👤 <b>Твой профиль</b>

<b>Основная информация:</b>
• Имя: {user.name}, {user.age}
• Город: {user.city or 'Не указан'}
• О себе: {user.bio or 'Не заполнено'}

<b>Статистика:</b>
• Лайков отправлено: {user.likes_sent}
• Лайков получено: {user.likes_received}
• Совпадений: {user.matches_count}
• Просмотров: {user.views_count}

<b>Активность:</b>
• Лайков на этой неделе: {stats.get('likes_this_week', 0)}
• Совпадений на этой неделе: {stats.get('matches_this_week', 0)}
• Просмотров на этой неделе: {stats.get('views_this_week', 0)}

<b>Подписка:</b> {user.subscription_type.upper()}
    """.strip()
    
    await callback.message.edit_text(
        profile_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀ Назад", callback_data="back")]
        ])
    )
    await callback.answer()


@dp.callback_query(F.data == "matches")
async def callback_matches(callback):
    """Show user matches"""
    user = await DatabaseManager.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    matches = await DatabaseManager.get_user_matches(user.id)
    
    if not matches:
        await callback.message.edit_text(
            "💕 <b>Твои совпадения</b>\n\n"
            "У тебя пока нет совпадений.\n\n"
            "Открой приложение и начни свайпать!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀ Назад", callback_data="back")]
            ])
        )
    else:
        text = f"💕 <b>Твои совпадения ({len(matches)})</b>\n\n"
        
        for match in matches[:10]:  # Show first 10 matches
            text += f"• {match['user'].name}, {match['user'].age}\n"
        
        if len(matches) > 10:
            text += f"\n... и еще {len(matches) - 10} совпадений"
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀ Назад", callback_data="back")]
            ])
        )
    
    await callback.answer()


@dp.callback_query(F.data == "referral")
async def callback_referral(callback):
    """Show referral program"""
    user = await DatabaseManager.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    ref_link = f"https://t.me/FFlirtly_bot?start=ref_{user.telegram_id}"
    stats = await DatabaseManager.get_referral_stats(user.id)
    
    await callback.message.edit_text(
        f"🎁 <b>Реферальная программа</b>\n\n"
        f"Приглашай друзей и получай бонусы!\n\n"
        f"<b>За каждого друга:</b>\n"
        f"• Ты получаешь: +10 лайков\n"
        f"• Друг получает: +5 лайков\n\n"
        f"<b>Твоя статистика:</b>\n"
        f"👥 Приглашено: {stats['total_referrals']}\n"
        f"❤️ Бонусных лайков: {user.bonus_likes}\n\n"
        f"<b>Твоя ссылка:</b>\n"
        f"<code>{ref_link}</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📤 Поделиться",
                    url=f"https://t.me/share/url?url={ref_link}&text=🔥 Попробуй Flirtly!"
                )
            ],
            [InlineKeyboardButton(text="◀ Назад", callback_data="back")]
        ])
    )
    await callback.answer()


@dp.callback_query(F.data == "premium")
async def callback_premium(callback):
    """Show premium options"""
    await callback.message.edit_text(
        "⭐ <b>Premium подписка</b>\n\n"
        "<b>🌟 PREMIUM (250 ⭐/месяц)</b>\n"
        "• Безлимитные лайки\n"
        "• 5 суперлайков/день\n"
        "• Расширенные фильтры\n"
        "• Видеть кто лайкнул\n\n"
        "<b>💎 PLATINUM (500 ⭐/месяц)</b>\n"
        "• Всё из Premium +\n"
        "• AI совместимость\n"
        "• Приоритет в показе\n"
        "• Инкогнито режим\n\n"
        "Оформи через Web App!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚡ Открыть Flirtly",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ],
            [InlineKeyboardButton(text="◀ Назад", callback_data="back")]
        ])
    )
    await callback.answer()


@dp.callback_query(F.data == "back")
async def callback_back(callback):
    """Back to main menu"""
    await callback.message.edit_text(
        f"<b>Привет, {callback.from_user.first_name}!</b>\n\n"
        f"Нажми кнопку ниже чтобы открыть Flirtly!",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


async def main():
    """Start bot with optimized database"""
    logger.info("Initializing optimized database...")
    await init_db()
    
    logger.info("Starting Flirtly Bot with optimized database operations...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
