# NovaChat 2.0

Полноценный Telegram-style frontend с реальным backend через Supabase.

## Возможности

- вход только по имени, без пароля
- анонимная авторизация Supabase
- реальные профили пользователей
- поиск пользователей
- реальные realtime-сообщения
- online/offline поле
- отправка файлов
- изображения/видео/аудио через Storage
- голосовые сообщения через MediaRecorder
- реакции ❤️ 🔥 😂
- browser notifications
- адаптивный мобильный интерфейс
- киношные CSS-анимации, aurora background, glass UI, message transitions
- GitHub Pages compatible
- без Node.js и сборки

## Настройка

1. Создайте проект Supabase.
2. В Authentication включите Anonymous Sign-Ins.
3. Откройте SQL Editor и выполните `supabase/schema.sql`.
4. В Project Settings -> API возьмите Project URL и anon key.
5. В `index.html` замените:

`YOUR_SUPABASE_URL`
`YOUR_SUPABASE_ANON_KEY`

6. Загрузите `index.html` на GitHub.
7. Включите GitHub Pages.

Важно: для production желательно добавить нормальную авторизацию, ограничения размера файлов, moderation/rate limits и более строгие Storage policies.

## Почему Supabase

GitHub Pages сам по себе не умеет быть сервером. Supabase дает БД, Realtime, Storage и Auth, поэтому статический frontend можно оставить на GitHub Pages, а backend работает отдельно.
