FROM ubuntu:22.04

# Intentionally misconfigured Linux target for privilege escalation practice.
# Lab use only.

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    python3 \
    curl \
    wget \
    netcat-openbsd \
    cron \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create low-privilege lab user
RUN useradd -m -s /bin/bash labuser && \
    echo "labuser:labpassword" | chpasswd

# Intentional misconfig: SUID binary for practice (find is already installed via findutils)
RUN cp /usr/bin/find /usr/local/bin/find_lab && \
    chmod u+s /usr/local/bin/find_lab

# Intentional misconfig: labuser can run python3 as root without password
RUN echo "labuser ALL=(root) NOPASSWD: /usr/bin/python3" >> /etc/sudoers

# Intentional misconfig: world-writable cron job running as root every minute
RUN printf '#!/bin/bash\necho "cleanup ran" >> /tmp/cleanup.log\n' > /opt/cleanup.sh && \
    chmod 777 /opt/cleanup.sh && \
    printf '* * * * * root /opt/cleanup.sh\n' > /etc/cron.d/cleanup && \
    chmod 644 /etc/cron.d/cleanup

# SSH setup
RUN mkdir -p /var/run/sshd && \
    echo "PermitRootLogin no" >> /etc/ssh/sshd_config && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config

# Drop flag for root to read
RUN mkdir -p /root && \
    echo "FLAG{root_privesc_complete}" > /root/flag.txt && \
    chmod 600 /root/flag.txt

EXPOSE 22

# Start cron and SSH
CMD ["bash", "-c", "service cron start && /usr/sbin/sshd -D"]
