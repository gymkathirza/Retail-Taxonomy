FROM node:20-alpine

WORKDIR /app

COPY apps/web/package.json apps/web/package-lock.json* /app/
RUN npm install

COPY apps/web /app

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
