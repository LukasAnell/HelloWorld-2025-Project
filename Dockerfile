FROM nginx:alpine
# Copy only the site server block into conf.d, do NOT overwrite /etc/nginx/nginx.conf
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf
COPY ./src/ /usr/share/nginx/html
EXPOSE 80