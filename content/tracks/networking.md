# Networking, HTTP, DNS & TLS Curriculum

## 1. What
Computer networking defines the protocols, encapsulation formats, and physical/logical routing mechanisms that allow disparate computing nodes to communicate reliably across local networks and the global Internet.

## 2. Why
Almost every high-severity production outage stems from networking failures: misconfigured DNS resolvers, silent firewall packet drops, MTU black holes, TCP connection pool exhaustion, expired TLS certificates, or HTTP/2 stream multiplexing bottlenecks.

## 3. Architecture
```
+-----------------------------------------------------------+
| Layer 7 (Application): HTTP/1.1, HTTP/2, gRPC, DNS, TLS   |
+-----------------------------------------------------------+
| Layer 4 (Transport): TCP (reliable, streams) | UDP (fast) |
+-----------------------------------------------------------+
| Layer 3 (Network): IPv4, IPv6, ICMP, IP Routing           |
+-----------------------------------------------------------+
| Layer 2 (Data Link): Ethernet, MAC addresses, ARP, VLANs  |
+-----------------------------------------------------------+
```

## 4. Internals
- **TCP 3-Way Handshake**: `SYN` -> `SYN-ACK` -> `ACK`. Kernel backlog queues: `SYN queue` (incomplete handshakes) and `Accept queue` (established connections waiting for application `accept()` syscall). If accept queue overflows (monitored via `netstat -s` or `ss -lnt`), incoming connection attempts are silently dropped or reset.
- **TCP Socket States**: `LISTEN`, `SYN_SENT`, `SYN_RECEIVED`, `ESTABLISHED`, `FIN_WAIT_1`, `FIN_WAIT_2`, `CLOSE_WAIT`, `CLOSING`, `LAST_ACK`, `TIME_WAIT`, `CLOSED`.
- **TIME_WAIT State**: Maintained for 2 * Maximum Segment Lifetime (typically 60s) by the endpoint that initiated the active close to ensure delayed packets drain from the network and ensure final ACK delivery. Excessive TIME_WAIT sockets cause ephemeral port starvation.
- **DNS Resolution Internals**: Resolver hierarchy (`/etc/resolv.conf` -> Local stub resolver -> Recursive resolver -> Root -> TLD -> Authoritative server). Record types: `A` (IPv4), `AAAA` (IPv6), `CNAME` (canonical alias), `SRV` (service port/weight), `PTR` (reverse lookup). The `ndots:5` configuration in Kubernetes pods causes high query amplification on external domains.
- **TLS 1.3 Handshake**: 1-RTT handshake providing forward secrecy via Ephemeral Diffie-Hellman (ECDHE). Certificate validation verifies: signature chain up to trusted root CA, hostname match (SAN: Subject Alternative Name), validity time window (`notBefore` to `notAfter`), and revocation status (OCSP stapling).

## 5. Commands
- Socket and connection analysis:
  - `ss -tulpn` (listening TCP/UDP sockets with process IDs)
  - `ss -s` (socket summary statistics)
  - `netstat -s | grep -i listen` (listen queue overflows)
  - `tcpdump -nnvv -i any port 80 -w capture.pcap`
- DNS debugging:
  - `dig +trace api.internal.corp`
  - `dig @127.0.0.1 -p 53 auth-service.prod.svc.cluster.local SRV`
  - `nslookup`, `getent hosts <hostname>`
- HTTP & TLS debugging:
  - `curl -vvv -IL https://api.corp.com`
  - `curl -w "@curl-format.txt" -o /dev/null -s https://api.corp.com` (timing breakdown: dns, connect, tls, starttransfer, total)
  - `openssl s_client -connect api.corp.com:443 -servername api.corp.com -showcerts`
  - `openssl x509 -in cert.pem -noout -text | grep -E "Issuer|Not After|Subject Alternative Name"`

## 6. Configuration
- `/etc/resolv.conf`:
  ```
  nameserver 10.96.0.10
  search prod.svc.cluster.local svc.cluster.local cluster.local
  options ndots:2 timeout:2 attempts:3
  ```
- Nginx / Envoy Keep-Alive:
  - `keepalive_timeout 65s;`
  - `keepalive_requests 1000;`

## 7. Hands-on Lab
- **Lab 1: DNS Resolution Latency & ndots Loop**: Trace DNS queries using `tcpdump`; observe query amplification on Alpine containers; remediate by adjusting `dnsConfig` to `ndots:2`.
- **Lab 2: MTU Discovery Black Hole**: Emulate jumbo frames traversing standard 1500-byte WAN link with Don't Fragment (DF) flag set; observe dropped packets; diagnose using `ping -M do -s 1472 <ip>`.
- **Lab 3: Expired Intermediate TLS Certificate**: Diagnose `SSLV3_ALERT_CERTIFICATE_EXPIRED`; extract and inspect x509 cert chain; replace with valid intermediate bundle.

## 8. Common Errors
- `Connection refused` (No process listening on the target IP:port, or backlog queue full with tcp_abort_on_overflow=1).
- `Connection reset by peer (ECONNRESET)` (Remote endpoint crashed, closed socket with unread bytes, or firewall dropped state).
- `SSL routines:certificate verify failed: certificate has expired`.
- `Name or service not known` / `NXDOMAIN`.

## 9. Troubleshooting
1. Verify L3 connectivity: `ping` or `traceroute` (ensure ICMP is permitted).
2. Verify L4 listening port and socket state: `nc -zv <ip> <port>` or `ss -tlpn`.
3. Verify TLS handshake and certificate chain: `openssl s_client`.
4. Inspect packet captures: `tcpdump -i any host <ip> and port <port>`.

## 10. Production Design
- Implement connection pooling at the application layer (e.g. keep-alive connection pools).
- Place caching DNS forwarders (NodeLocal DNSCache) on every cluster node.
- Automate TLS certificate provisioning and renewal via Let's Encrypt / Vault with alerting 30 days before expiration.

## 11. Security
- Enforce mTLS (mutual TLS) for internal service-to-service communication.
- Restrict egress traffic using strict firewall and NetworkPolicy egress whitelists.
- Disable outdated cipher suites and protocols (SSLv3, TLS 1.0, TLS 1.1).

## 12. Performance
- Enable TCP BBR congestion control (`net.ipv4.tcp_congestion_control = bbr`).
- Reuse TIME_WAIT sockets for outgoing connections (`net.ipv4.tcp_tw_reuse = 1`).
- Optimize TCP window scaling and receive/send buffer sizes for high-bandwidth WAN links.

## 13. Interview Scenarios
- **Scenario**: A microservice starts throwing `dial tcp: lookup auth-service: i/o timeout` during peak traffic. The DNS server is healthy. What is happening?
  - **Answer**: Kernel conntrack table saturation or UDP buffer packet drops. Under high concurrency, Linux conntrack (`/proc/sys/net/netfilter/nf_conntrack_max`) fills up, dropping subsequent UDP packets. Alternatively, CoreDNS is overwhelmed by `ndots:5` amplification.
