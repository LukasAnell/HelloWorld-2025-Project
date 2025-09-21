# Use the official lightweight Nginx image

FROM nginx:alpine

# Copy the static website content

COPY ./src/ /usr/share/nginx/html

# Copy the Nginx configuration file

# COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf

# Expose port 80

EXPOSE 80
