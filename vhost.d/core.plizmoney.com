location /static/ {
    alias /app/staticfiles/;
    access_log off;
    expires 30d;
}

location /media/ {
    alias /app/media/;
    access_log off;
    expires 30d;
}

ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers on;
