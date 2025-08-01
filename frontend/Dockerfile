# Этап 1: Сборка приложения
FROM node:18-alpine as builder

WORKDIR /app

# Копируем package файлы
COPY package*.json ./

# Очищаем npm кэш и устанавливаем зависимости заново для исправления ARM64 проблемы
RUN npm cache clean --force
RUN rm -rf node_modules package-lock.json
RUN npm install

# Копируем исходный код
COPY . .

# Собираем приложение для production
RUN npm run build

# Этап 2: Production образ с nginx
FROM nginx:alpine

# Копируем собранное приложение
COPY --from=builder /app/dist /usr/share/nginx/html

# Копируем конфигурацию nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открываем порт
EXPOSE 80

# Запускаем nginx
CMD ["nginx", "-g", "daemon off;"]