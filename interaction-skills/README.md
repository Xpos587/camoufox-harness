# Debian 13

## Шпаргалка

### Настройка сети

```bash
# Отключение IPv6 для стабильности работы Docker
echo 'net.ipv6.conf.all.disable_ipv6 = 1' >> /etc/sysctl.conf
echo 'net.ipv6.conf.default.disable_ipv6 = 1' >> /etc/sysctl.conf
sysctl -p
```

### Настройка DNS у доменного провайдера

1. Откройте панель управления вашего доменного провайдера
2. Добавьте следующие DNS записи:
   ```
   A:     {SUB_DOMAIN}.{DOMAIN}     → {IP_ADDRESS}
   CNAME: *.{SUB_DOMAIN}.{DOMAIN}  → {SUB_DOMAIN}.{DOMAIN}
   ```
3. **Время применения:** от 1 минуты до 24 часов для глобального обновления DNS

#### Проверка DNS записей

```bash
# Проверка A записи
dig {SUB_DOMAIN}.{DOMAIN} A

# Проверка CNAME записи
dig portainer.{SUB_DOMAIN}.{DOMAIN} CNAME
```

### Установка must-have пакетов

```bash
apt update && apt upgrade -y
apt install -y sudo           # Позволяет выполнять команды от имени суперпользователя
sudo apt install -y btop      # Удобный диспетчер задач с поддержкой GPU
sudo apt install -y iproute2  # Набор инструментов для управления сетевыми интерфейсами и маршрутизацией
sudo apt install -y net-tools # Классические сетевые утилиты (ifconfig, netstat и др.)
sudo apt install -y netcat-openbsd  # Утилита netcat для работы с сетевыми соединениями
sudo apt install -y dnsutils  # Инструменты для работы с DNS (dig, nslookup и др.)
sudo apt install -y neovim    # Современная версия текстового редактора Vim
sudo apt install -y jq        # Утилита для обработки JSON в командной строке
sudo apt install -y ncdu      # Анализатор дискового пространства с интерфейсом ncurses
sudo apt install -y unzip     # Утилита для распаковки ZIP-архивов
sudo apt install -y ufw       # Uncomplicated Firewall для простого управления фаерволом
sudo apt install -y speedtest-cli
sudo apt install -y zram-tools
```

### ZRAM

```sh
sudo tee /etc/default/zramswap <<'EOF'
# Алгоритм сжатия: zstd (оптимально по скорости и эффективности)
ALGO=zstd
# 50% от ОЗУ = 2ГБ сжатой памяти (эквивалент ~4ГБ реальных данных)
PERCENT=50
# Приоритет: 100 = использовать ZRAM ПЕРЕД дисковым swap
PRIORITY=100
EOF

# Перезапуск службы и включение автозапуска

sudo systemctl restart zramswap.service
sudo systemctl enable zramswap.service

# Проверка работы ZRAM

zramctl
free -h | grep -E 'Mem|Swap'
```

### Конфигурация дискового SWAP (страховка при нехватке RAM)

```sh
# Создание swap-файла 4ГБ (на диске, работает вместе с ZRAM)
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo "/swapfile swap swap defaults 0 0" | sudo tee -a /etc/fstab

# Проверка
swapon --show
free -h | grep Swap
```

#### Настройка swappiness (приоритет использования swap)

```sh
# 60 = использовать swap при заполнении RAM на ~40% (оптимально для ZRAM + swap)
sudo sysctl vm.swappiness=60
echo "vm.swappiness=60" | sudo tee -a /etc/sysctl.conf

# Проверка
sysctl vm.swappiness
```

### Docker

```sh
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt-get remove $pkg; done
```

```sh
# Add Docker's official GPG key:
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
```

```sh
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
