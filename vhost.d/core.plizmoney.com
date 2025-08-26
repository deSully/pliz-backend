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


# Protocoles TLS supportés (inclut TLSv1.1 pour compatibilité avec anciens clients)
ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;

# Cipher suites compatibles modernes et anciens clients
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:
ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:
ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:
AES128-SHA:AES256-SHA:DES-CBC3-SHA';
ssl_prefer_server_ciphers on;

# Optionnel : activer session cache pour performance
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
