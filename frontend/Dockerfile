# Use an official Nginx runtime as a parent image
FROM nginx:1.25-alpine-slim

# Set the working directory in Nginx (though not strictly necessary for simple copy)
# WORKDIR /usr/share/nginx/html

# Remove default Nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy static assets from the frontend folder to Nginx's default serve directory
COPY index.html /usr/share/nginx/html/
COPY style.css /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/
COPY api.js /usr/share/nginx/html/
COPY ui.js /usr/share/nginx/html/
COPY socketService.js /usr/share/nginx/html/
# If there were other assets like images, they would be copied here too.
# For example: COPY images/ /usr/share/nginx/html/images/

# (Optional) Copy a custom Nginx configuration file if needed
# For this basic setup, the default Nginx configuration to serve static files
# from /usr/share/nginx/html on port 80 is usually sufficient.
# If a custom config is needed (e.g., for SPA routing or proxying):
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 (Nginx default port)
EXPOSE 80

# Command to run Nginx in the foreground
# This is the default command for the Nginx image, but explicitly stating it is good practice.
CMD ["nginx", "-g", "daemon off;"]
