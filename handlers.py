from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from texts import get_text

router = Router()

# Состояния для FSM
class PaymentStates(StatesGroup):
    waiting_for_amount = State()

class PromptStates(StatesGroup):
    waiting_for_custom_prompt = State()

class GenerationStates(StatesGroup):
    waiting_for_photo = State()

def get_language_keyboard():
    """Создает клавиатуру для выбора языка"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский", callback_data="lang_ru")
    builder.button(text="🇺🇸 English", callback_data="lang_en")
    builder.adjust(2)
    return builder.as_markup()

def get_main_menu_keyboard(language):
    """Создает главное меню"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text(language, "send_photo"), 
        callback_data="send_photo"
    )
    builder.button(
        text=get_text(language, "settings"), 
        callback_data="settings"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_settings_keyboard(language, balance):
    """Создает клавиатуру настроек"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text(language, "top_up_balance"), 
        callback_data="top_up_balance"
    )
    builder.button(
        text=get_text(language, "change_language"), 
        callback_data="change_language"
    )
    builder.button(
        text=get_text(language, "back_to_menu"), 
        callback_data="back_to_menu"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_payment_methods_keyboard(language):
    """Создает клавиатуру для выбора способа оплаты"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text(language, "yookassa"), 
        callback_data="payment_yookassa"
    )
    builder.button(
        text=get_text(language, "card_transfer"), 
        callback_data="payment_card"
    )
    builder.button(
        text=get_text(language, "sbp"), 
        callback_data="payment_sbp"
    )
    builder.button(
        text=get_text(language, "back_to_settings"), 
        callback_data="back_to_settings"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_templates_keyboard(language, page=0):
    """Создает клавиатуру для выбора шаблонов с пагинацией"""
    templates_per_page = 5
    total_templates = 20
    total_pages = (total_templates + templates_per_page - 1) // templates_per_page
    
    builder = InlineKeyboardBuilder()
    
    # Добавляем шаблоны для текущей страницы
    start_template = page * templates_per_page + 1
    end_template = min(start_template + templates_per_page - 1, total_templates)
    
    for i in range(start_template, end_template + 1):
        builder.button(
            text=get_text(language, f"template_{i}"), 
            callback_data=f"template_{i}"
        )
    
    # Добавляем кнопки "Свой промпт" и "Назад в меню" на каждую страницу
    builder.button(
        text=get_text(language, "custom_prompt"), 
        callback_data="custom_prompt"
    )
    builder.button(
        text=get_text(language, "back_to_menu"), 
        callback_data="back_to_menu"
    )
    
    # Добавляем навигацию по страницам
    if total_pages > 1:
        nav_row = []
        
        # Кнопка "Предыдущая страница"
        if page > 0:
            nav_row.append(("⬅️", f"templates_page_{page - 1}"))
        
        # Индикатор текущей страницы
        nav_row.append((f"{page + 1}/{total_pages}", "current_page"))
        
        # Кнопка "Следующая страница"
        if page < total_pages - 1:
            nav_row.append(("➡️", f"templates_page_{page + 1}"))
        
        # Добавляем кнопки навигации
        for text, callback_data in nav_row:
            if callback_data != "current_page":  # Пропускаем индикатор страницы
                builder.button(text=text, callback_data=callback_data)
    
    # Настраиваем расположение: шаблоны по одному в ряд, затем 2 кнопки в ряд, затем навигация
    layout = [1] * (end_template - start_template + 1) + [2] + [len(nav_row) if total_pages > 1 else 0]
    builder.adjust(*[x for x in layout if x > 0])
    
    return builder.as_markup()

def get_custom_prompt_keyboard(language):
    """Создает клавиатуру для ввода собственного промпта"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text(language, "back_to_templates"), 
        callback_data="back_to_templates"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_prompt_review_keyboard(language):
    """Создает клавиатуру для просмотра промпта с предложением улучшить"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text(language, "improve_prompt"), 
        callback_data="improve_prompt"
    )
    builder.button(
        text=get_text(language, "keep_my_prompt"), 
        callback_data="keep_my_prompt"
    )
    builder.button(
        text=get_text(language, "back_to_templates"), 
        callback_data="back_to_templates"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_generation_result_keyboard(language):
    """Создает клавиатуру для результата генерации"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text(language, "try_again"), 
        callback_data="try_again"
    )
    builder.button(
        text=get_text(language, "send_another_photo"), 
        callback_data="send_another_photo"
    )
    builder.button(
        text=get_text(language, "menu"), 
        callback_data="back_to_menu"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_insufficient_balance_keyboard(language: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру для случаев недостатка баланса"""
    keyboard = [
        [InlineKeyboardButton(
            text=get_text(language, "top_up_balance_button"),
            callback_data="top_up_balance"
        )],
        [InlineKeyboardButton(
            text=get_text(language, "main_menu_button"),
            callback_data="back_to_menu"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    
    if db.is_new_user(user_id):
        # Новый пользователь - предлагаем выбрать язык
        await message.answer(
            get_text("ru", "welcome_new"),
            reply_markup=get_language_keyboard()
        )
    else:
        # Существующий пользователь - показываем главное меню
        language = db.get_user_language(user_id)
        await message.answer(
            get_text(language, "welcome_back"),
            reply_markup=get_main_menu_keyboard(language)
        )

@router.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery):
    user_id = callback.from_user.id
    language = callback.data.split("_")[1]
    
    if db.is_new_user(user_id):
        # Новый пользователь - добавляем в базу данных
        db.add_user(user_id, language)
    else:
        # Существующий пользователь - обновляет язык
        db.update_user_language(user_id, language)
    
    # Показываем главное меню
    await callback.message.edit_text(
        get_text(language, "language_selected")
    )
    await callback.message.answer(
        get_text(language, "welcome_back"),
        reply_markup=get_main_menu_keyboard(language)
    )
    
    await callback.answer()

@router.callback_query(F.data == "send_photo")
async def send_photo_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    
    # Показываем выбор шаблонов (первая страница)
    await callback.message.edit_text(
        get_text(language, "select_template"),
        reply_markup=get_templates_keyboard(language, page=0)
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("templates_page_"))
async def templates_page_handler(callback: CallbackQuery):
    """Обработчик для навигации по страницам шаблонов"""
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    
    # Получаем номер страницы
    page = int(callback.data.split("_")[-1])
    
    # Показываем выбранную страницу шаблонов
    await callback.message.edit_text(
        get_text(language, "select_template"),
        reply_markup=get_templates_keyboard(language, page=page)
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("template_"))
async def template_selected(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    template = callback.data.split("_")[1]
    balance = db.get_user_balance(user_id)
    
    # Проверяем баланс для генерации
    if balance < 50:
        await callback.answer(
            get_text(language, "insufficient_balance_generation", balance=balance)
        )
        await callback.message.answer(
            get_text(language, "top_up_balance_suggestion"),
            reply_markup=get_insufficient_balance_keyboard(language)
        )
        return
    
    # Сохраняем выбранный шаблон
    await state.update_data(selected_template=template, prompt_type="template")
    
    # Переходим к ожиданию фото
    await state.set_state(GenerationStates.waiting_for_photo)
    
    await callback.message.edit_text(
        get_text(language, "send_photo_for_generation", balance=balance)
    )
    
    await callback.answer()

@router.callback_query(F.data == "custom_prompt")
async def custom_prompt_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    
    # Переходим к вводу собственного промпта
    await state.set_state(PromptStates.waiting_for_custom_prompt)
    
    await callback.message.edit_text(
        get_text(language, "enter_custom_prompt"),
        reply_markup=get_custom_prompt_keyboard(language)
    )
    
    await callback.answer()

@router.message(PromptStates.waiting_for_custom_prompt)
async def process_custom_prompt(message: Message, state: FSMContext):
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    # Сохраняем введенный промпт
    await state.update_data(custom_prompt=message.text, prompt_type="custom")
    
    # Показываем промпт пользователя и предлагаем улучшить
    await message.answer(
        get_text(language, "your_prompt", prompt=message.text),
        reply_markup=get_prompt_review_keyboard(language)
    )

@router.callback_query(F.data == "improve_prompt")
async def improve_prompt_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    balance = db.get_user_balance(user_id)
    
    # Проверяем баланс
    if balance < 15:
        await callback.answer(
            get_text(language, "insufficient_balance", balance=balance)
        )
        await callback.message.answer(
            get_text(language, "top_up_balance_suggestion"),
            reply_markup=get_insufficient_balance_keyboard(language)
        )
        return
    
    # Получаем сохраненный промпт
    data = await state.get_data()
    custom_prompt = data.get("custom_prompt", "")
    
    if custom_prompt:
        # Списываем 15 кредитов
        success, new_balance = db.deduct_credits(user_id, 15)
        
        if success:
            # Здесь будет логика улучшения промпта
            improved_prompt = f"Улучшенная версия: {custom_prompt} (профессиональный стиль, детальное описание)"
            
            await callback.message.edit_text(
                f"{get_text(language, 'prompt_improved')}\n\n{improved_prompt}\n\n💰 Новый баланс: {new_balance} кредитов"
            )
            
            # Обновляем промпт в состоянии
            await state.update_data(custom_prompt=improved_prompt)
            
            # Переходим к ожиданию фото
            await state.set_state(GenerationStates.waiting_for_photo)
            
            await callback.message.answer(
                get_text(language, "send_photo_for_generation", balance=new_balance)
            )
        else:
            await callback.answer("Ошибка при списании кредитов!")
    else:
        await callback.answer("Сначала введите промпт!")
    
    await callback.answer()

@router.callback_query(F.data == "keep_my_prompt")
async def keep_my_prompt_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    balance = db.get_user_balance(user_id)
    
    # Проверяем баланс для генерации
    if balance < 50:
        await callback.answer(
            get_text(language, "insufficient_balance_generation", balance=balance)
        )
        await callback.message.answer(
            get_text(language, "top_up_balance_suggestion"),
            reply_markup=get_insufficient_balance_keyboard(language)
        )
        return
    
    # Получаем сохраненный промпт
    data = await state.get_data()
    custom_prompt = data.get("custom_prompt", "")
    
    if custom_prompt:
        # Показываем сообщение о том, что промпт оставлен как есть
        await callback.message.edit_text(
            f"✅ Ваш промпт оставлен без изменений:\n\n{custom_prompt}"
        )
        
        # Переходим к ожиданию фото
        await state.set_state(GenerationStates.waiting_for_photo)
        
        await callback.message.answer(
            get_text(language, "send_photo_for_generation", balance=balance)
        )
    else:
        await callback.answer("Сначала введите промпт!")
    
    await callback.answer()

@router.callback_query(F.data == "back_to_templates")
async def back_to_templates_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    
    # Очищаем состояние
    await state.clear()
    
    # Возвращаемся к выбору шаблонов (первая страница)
    await callback.message.edit_text(
        get_text(language, "select_template"),
        reply_markup=get_templates_keyboard(language, page=0)
    )
    
    await callback.answer()

@router.message(GenerationStates.waiting_for_photo)
async def process_photo_for_generation(message: Message, state: FSMContext):
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    balance = db.get_user_balance(user_id)
    
    # Проверяем, что это фото
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фото!")
        return
    
    # Проверяем баланс для генерации
    if balance < 50:
        await message.answer(
            get_text(language, "insufficient_balance_generation", balance=balance)
        )
        await message.answer(
            get_text(language, "top_up_balance_suggestion"),
            reply_markup=get_insufficient_balance_keyboard(language)
        )
        return
    
    # Списываем 50 кредитов за генерацию
    success, new_balance = db.deduct_credits(user_id, 50)
    
    if not success:
        await message.answer("Ошибка при списании кредитов!")
        return
    
    # Показываем сообщение о начале генерации
    await message.answer(get_text(language, "generation_in_progress"))
    
    try:
        # Здесь будет логика генерации изображения
        # Пока что просто симулируем успешную генерацию
        
        # Получаем данные о промпте
        data = await state.get_data()
        prompt_type = data.get("prompt_type")
        
        if prompt_type == "template":
            template = data.get("selected_template")
            prompt_info = f"Шаблон: {template}"
        else:
            custom_prompt = data.get("custom_prompt", "")
            prompt_info = f"Промпт: {custom_prompt}"
        
        # Показываем результат (пока исходное фото)
        await message.answer_photo(
            photo=message.photo[-1].file_id,
            caption=f"{get_text(language, 'generation_success')}\n\n{prompt_info}\n\n💰 Новый баланс: {new_balance} кредитов"
        )
        
        # Показываем клавиатуру с результатом
        await message.answer(
            "Выберите действие:",
            reply_markup=get_generation_result_keyboard(language)
        )
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        # При ошибке возвращаем списанные кредиты
        db.add_balance(user_id, 50)
        restored_balance = db.get_user_balance(user_id)
        
        # Уведомляем о возврате кредитов
        await message.answer(get_text(language, "credits_refunded"))
        
        # Обработка ошибки
        await message.answer(get_text(language, "generation_error"))
        
        # Возвращаем в главное меню
        await message.answer(
            get_text(language, "welcome_back"),
            reply_markup=get_main_menu_keyboard(language)
        )
        
        # Очищаем состояние
        await state.clear()

@router.callback_query(F.data == "try_again")
async def try_again_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    balance = db.get_user_balance(user_id)
    
    # Проверяем баланс для повторной генерации
    if balance < 50:
        await callback.answer(
            get_text(language, "insufficient_balance_generation", balance=balance)
        )
        await callback.message.answer(
            get_text(language, "top_up_balance_suggestion"),
            reply_markup=get_insufficient_balance_keyboard(language)
        )
        return
    
    # Списываем 50 кредитов за повторную генерацию
    success, new_balance = db.deduct_credits(user_id, 50)
    
    if not success:
        await callback.answer("Ошибка при списании кредитов!")
        return
    
    # Показываем сообщение о начале генерации
    await callback.message.edit_text(
        f"{get_text(language, 'generation_in_progress')}\n\n💰 Новый баланс: {new_balance} кредитов"
    )
    
    try:
        # Здесь будет логика повторной генерации изображения
        # Пока что просто симулируем успешную генерацию
        
        # Получаем данные о промпте из предыдущего состояния
        # (нужно будет сохранить их в отдельном месте или передать через callback_data)
        
        # Показываем результат (пока исходное фото)
        await callback.message.answer_photo(
            photo=callback.message.reply_to_message.photo[-1].file_id if callback.message.reply_to_message and callback.message.reply_to_message.photo else None,
            caption=f"{get_text(language, 'generation_success')}\n\n💰 Новый баланс: {new_balance} кредитов"
        )
        
        # Показываем клавиатуру с результатом
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_generation_result_keyboard(language)
        )
        
    except Exception as e:
        # При ошибке возвращаем списанные кредиты
        db.add_balance(user_id, 50)
        restored_balance = db.get_user_balance(user_id)
        
        # Уведомляем о возврате кредитов
        await callback.message.answer(get_text(language, "credits_refunded"))
        
        # Обработка ошибки
        await callback.message.answer(get_text(language, "generation_error"))
        
        # Возвращаем в главное меню
        await callback.message.answer(
            get_text(language, "welcome_back"),
            reply_markup=get_main_menu_keyboard(language)
        )
    
    await callback.answer()

@router.callback_query(F.data == "send_another_photo")
async def send_another_photo_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    balance = db.get_user_balance(user_id)
    
    # Проверяем баланс для генерации
    if balance < 50:
        await callback.answer(
            get_text(language, "insufficient_balance_generation", balance=balance)
        )
        await callback.message.answer(
            get_text(language, "top_up_balance_suggestion"),
            reply_markup=get_insufficient_balance_keyboard(language)
        )
        return
    
    # Переходим к ожиданию фото
    await state.set_state(GenerationStates.waiting_for_photo)
    
    await callback.message.edit_text(
        get_text(language, "send_photo_for_generation", balance=balance)
    )
    
    await callback.answer()

@router.callback_query(F.data == "settings")
async def settings_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    balance = db.get_user_balance(user_id)
    
    # Показываем профиль пользователя
    profile_text = f"{get_text(language, 'profile')}\n\n{get_text(language, 'balance', balance=balance)}"
    
    await callback.message.edit_text(
        profile_text,
        reply_markup=get_settings_keyboard(language, balance)
    )
    
    await callback.answer()

@router.callback_query(F.data == "top_up_balance")
async def top_up_balance_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    
    # Показываем выбор способа оплаты
    await callback.message.edit_text(
        get_text(language, "select_payment_method"),
        reply_markup=get_payment_methods_keyboard(language)
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("payment_"))
async def payment_method_selected(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    payment_method = callback.data.split("_")[1]
    
    # Сохраняем выбранный способ оплаты
    await state.update_data(payment_method=payment_method)
    
    # Переходим к вводу суммы
    await state.set_state(PaymentStates.waiting_for_amount)
    
    await callback.message.edit_text(
        get_text(language, "enter_amount")
    )
    
    await callback.answer()

@router.message(PaymentStates.waiting_for_amount)
async def process_payment_amount(message: Message, state: FSMContext):
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    try:
        amount = float(message.text)
        if amount <= 0:
            await message.answer(get_text(language, "amount_error"))
            return
        
        # Получаем сохраненный способ оплаты
        data = await state.get_data()
        payment_method = data.get("payment_method")
        
        # Пополняем баланс на введенную сумму
        new_balance = db.add_balance(user_id, amount)
        
        # Показываем сообщение об успешном пополнении
        await message.answer(
            get_text(language, "balance_topped_up", amount=amount, new_balance=new_balance)
        )
        
        # Очищаем состояние
        await state.clear()
        
        # Возвращаемся в настройки
        profile_text = f"{get_text(language, 'profile')}\n\n{get_text(language, 'balance', balance=new_balance)}"
        
        await message.answer(
            profile_text,
            reply_markup=get_settings_keyboard(language, new_balance)
        )
        
    except ValueError:
        await message.answer(get_text(language, "amount_error"))

@router.callback_query(F.data == "change_language")
async def change_language_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    current_language = db.get_user_language(user_id)
    
    # Показываем выбор языка
    await callback.message.edit_text(
        get_text(current_language, "select_new_language"),
        reply_markup=get_language_keyboard()
    )
    
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    
    # Возвращаемся в главное меню
    await callback.message.edit_text(
        get_text(language, "welcome_back"),
        reply_markup=get_main_menu_keyboard(language)
    )
    
    await callback.answer()

@router.callback_query(F.data == "back_to_settings")
async def back_to_settings_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    language = db.get_user_language(user_id)
    balance = db.get_user_balance(user_id)
    
    # Возвращаемся в настройки
    profile_text = f"{get_text(language, 'profile')}\n\n{get_text(language, 'balance', balance=balance)}"
    
    await callback.message.answer(
        profile_text,
        reply_markup=get_settings_keyboard(language, balance)
    )
    
    await callback.answer()

def register_handlers(dp):
    """Регистрирует все обработчики"""
    dp.include_router(router)
