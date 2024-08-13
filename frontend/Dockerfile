# Use the official Nginx image as a base
FROM nginx:alpine

# Remove the default Nginx welcome page
RUN rm /usr/share/nginx/html/index.html

COPY . /usr/share/nginx/html/

# Expose port 80 to allow access to the web server
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]

