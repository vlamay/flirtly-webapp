# src/bot_full.py - Full bot with database integration

import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import (
    init_db, async_session_maker, 
    User, get_or_create_user, get_user_by_telegram_id
)
from src.matching import MatchingEngine
from src.features import ReferralSystem

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
    """Main keyboard"""
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
    """Start command with referral handling"""
    async with async_session_maker() as session:
        telegram_id = message.from_user.id
        username = message.from_user.username
        
        # Get or create user
        user = await get_or_create_user(telegram_id, username, session)
        
        # Handle referral
        args = message.text.split()
        if len(args) > 1 and args[1].startswith("ref_"):
            try:
                referrer_telegram_id = int(args[1].replace("ref_", ""))
                referrer = await get_user_by_telegram_id(referrer_telegram_id, session)
                
                if referrer and referrer.id != user.id:
                    # Process referral
                    result = await ReferralSystem.process_referral(
                        referrer.id,
                        user.id,
                        session
                    )
                    
                    if result['success']:
                        # Notify referrer
                        try:
                            await bot.send_message(
                                referrer.telegram_id,
                                f"🎁 <b>Новый реферал!</b>\n\n"
                                f"@{username or 'пользователь'} зарегистрировался по твоей ссылке!\n\n"
                                f"Ты получил +{result['referrer_bonus']} лайков! ❤️",
                                parse_mode="HTML"
                            )
                        except:
                            pass
            except:
                pass
        
        # Check if profile is complete
        if not user.name or not user.photos:
            # New user - needs onboarding
            await message.answer(
                f"<b>Привет, {message.from_user.first_name}! 👋</b>\n\n"
                f"Добро пожаловать в <b>Flirtly</b> ⚡\n\n"
                f"Нажми кнопку ниже чтобы создать профиль и начать знакомиться!",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
        else:
            # Existing user
            await message.answer(
                f"<b>С возвращением, {user.name}! 👋</b>\n\n"
                f"<b>Твоя статистика:</b>\n"
                f"• ❤️ Лайков осталось: {user.daily_likes_remaining}\n"
                f"• 💕 Совпадений: {user.matches_count}\n"
                f"• 👀 Просмотров профиля: {user.views_count}\n\n"
                f"Открой приложение и продолжай свайп!",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )


@dp.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    """Handle data from Web App"""
    import json
    
    async with async_session_maker() as session:
        try:
            data = json.loads(message.web_app_data.data)
            action = data.get('action')
            telegram_id = message.from_user.id
            
            user = await get_user_by_telegram_id(telegram_id, session)
            if not user:
                user = await get_or_create_user(telegram_id, message.from_user.username, session)
            
            if action == 'register':
                # Handle registration
                user.name = data.get('name')
                user.age = data.get('age')
                user.gender = data.get('gender')
                user.looking_for = data.get('looking_for')
                user.bio = data.get('bio', '')
                user.photos = ','.join(data.get('photos', []))
                
                # Location
                user.city = data.get('city')
                user.country = data.get('country')
                user.latitude = data.get('latitude')
                user.longitude = data.get('longitude')
                
                await session.commit()
                
                await message.answer(
                    f"🎉 <b>Регистрация завершена!</b>\n\n"
                    f"Добро пожаловать, {user.name}!\n\n"
                    f"📍 Местоположение: {user.city or 'Не указано'}\n\n"
                    f"Теперь можешь начать искать совпадения! ⚡",
                    parse_mode="HTML"
                )
            
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
                
                # Process like
                result = await MatchingEngine.process_like(
                    user,
                    profile_id,
                    is_super_like,
                    session
                )
                
                if result['is_match']:
                    # Match created!
                    matched_user = result['matched_user']
                    
                    await message.answer(
                        f"🎉 <b>Это Match!</b>\n\n"
                        f"Вы понравились друг другу с {matched_user.name}!\n\n"
                        f"Теперь можете начать общаться! 💬",
                        parse_mode="HTML"
                    )
                    
                    # Notify matched user
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
            
            elif action == 'skip':
                profile_id = data.get('profile_id')
                
                await MatchingEngine.process_skip(user, profile_id, session)
                await message.answer("👎 Пропущено")
            
        except Exception as e:
            logger.error(f"Error handling webapp data: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка")


@dp.callback_query(F.data == "profile")
async def callback_profile(callback):
    """Show profile"""
    async with async_session_maker() as session:
        user = await get_user_by_telegram_id(callback.from_user.id, session)
        
        if not user or not user.name:
            await callback.answer("Сначала создай профиль!", show_alert=True)
            return
        
        profile_text = (
            f"👤 <b>Твой профиль</b>\n\n"
            f"<b>Имя:</b> {user.name}, {user.age}\n"
            f"<b>Город:</b> {user.city or 'Не указан'}\n"
            f"<b>О себе:</b> {user.bio or 'Не заполнено'}\n\n"
            f"<b>Статистика:</b>\n"
            f"• Лайков отправлено: {user.likes_sent}\n"
            f"• Лайков получено: {user.likes_received}\n"
            f"• Совпадений: {user.matches_count}\n"
            f"• Просмотров: {user.views_count}\n\n"
            f"<b>Подписка:</b> {user.subscription_type.value.upper()}"
        )
        
        await callback.message.edit_text(
            profile_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀ anback", callback_data="back")]
            ])
        )
    await callback.answer()


@dp.callback_query(F.data == "matches")
async def callback_matches(callback):
    """Show matches"""
    async with async_session_maker() as session:
        from sqlalchemy import select, or_
        from src.database import Match
        
        user = await get_user_by_telegram_id(callback.from_user.id, session)
        
        if not user:
            await callback.answer("Ошибка", show_alert=True)
            return
        
        # Get matches
        result = await session.execute(
            select(Match).where(
                or_(
                    Match.user1_id == user.id,
                    Match.user2_id == user.id
                ),
                Match.is_active == True
            ).order_by(Match.created_at.desc())
        )
        matches = result.scalars().all()
        
        if not matches:
            await callback.message.edit_text(
                "💕 <b>Твои совпадения</b>\n\n"
                "У тебя пока нет совпадений.\n\n"
                "Открой приложение и начни свайпать!",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀ anback", callback_data="back")]
                ])
            )
        else:
            text = f"💕 <b>Твои совпадения ({len(matches)})</b>\n\n"
            
            for match in matches[:10]:
                matched_user_id = match.user2_id if match.user1_id == user.id else match.user1_id
                matched_user = await session.get(User, matched_user_id)
                
                if matched_user:
                    text += f"• {matched_user.name}, {matched_user.age}\n"
            
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀ anback", callback_data="back")]
                ])
            )
    
    await callback.answer()


@dp.callback_query(F.data == "referral")
async def callback_referral(callback):
    """Show referral program"""
    async with async_session_maker() as session:
        user = await get_user_by_telegram_id(callback.from_user.id, session)
        
        if not user:
            await callback.answer("Ошибка", show_alert=True)
            return
        
        ref_link = ReferralSystem.generate_referral_link(user.telegram_id)
        
        # Get referral stats
        stats = await ReferralSystem.get_referral_stats(user.id, session)
        
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
                [InlineKeyboardButton(text="◀ anback", callback_data="back")]
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
            [InlineKeyboardButton(text="◀ anback", callback_data="back")]
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
    """Start bot"""
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Starting Flirtly Bot with full database integration...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
