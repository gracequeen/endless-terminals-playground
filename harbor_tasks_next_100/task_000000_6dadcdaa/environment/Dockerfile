FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    sqlite3 \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/builds && chmod 0777 /home/user && chmod 0777 /home/user/builds

RUN sqlite3 /home/user/builds/artifacts.db "CREATE TABLE build_artifacts ( \
    id INTEGER PRIMARY KEY, \
    build_id TEXT, \
    path TEXT, \
    size_bytes INTEGER, \
    created_at TEXT \
);"

RUN sqlite3 /home/user/builds/artifacts.db " \
INSERT INTO build_artifacts (build_id, path, size_bytes, created_at) VALUES \
('build-001', '/artifacts/build-001/app.tar.gz', 524288000, '2024-01-15 10:30:00'), \
('build-002', '/artifacts/build-002/app.tar.gz', 498765432, '2024-01-15 11:00:00'), \
('build-003', '/artifacts/build-003/app.tar.gz', 475000000, '2024-01-15 11:30:00'), \
('build-004', '/artifacts/build-004/app.tar.gz', 450123456, '2024-01-15 12:00:00'), \
('build-005', '/artifacts/build-005/app.tar.gz', 425000000, '2024-01-15 12:30:00'), \
('build-006', '/artifacts/build-006/app.tar.gz', 400987654, '2024-01-15 13:00:00'), \
('build-007', '/artifacts/build-007/app.tar.gz', 375000000, '2024-01-15 13:30:00'), \
('build-008', '/artifacts/build-008/app.tar.gz', 350654321, '2024-01-15 14:00:00'), \
('build-009', '/artifacts/build-009/app.tar.gz', 325000000, '2024-01-15 14:30:00'), \
('build-010', '/artifacts/build-010/app.tar.gz', 300111222, '2024-01-15 15:00:00'), \
('build-011', '/artifacts/build-011/app.tar.gz', 275000000, '2024-01-16 10:00:00'), \
('build-012', '/artifacts/build-012/app.tar.gz', 250333444, '2024-01-16 10:30:00'), \
('build-013', '/artifacts/build-013/app.tar.gz', 225000000, '2024-01-16 11:00:00'), \
('build-014', '/artifacts/build-014/app.tar.gz', 200555666, '2024-01-16 11:30:00'), \
('build-015', '/artifacts/build-015/app.tar.gz', 175000000, '2024-01-16 12:00:00'), \
('build-016', '/artifacts/build-016/app.tar.gz', 150777888, '2024-01-16 12:30:00'), \
('build-017', '/artifacts/build-017/app.tar.gz', 125000000, '2024-01-16 13:00:00'), \
('build-018', '/artifacts/build-018/app.tar.gz', 100999111, '2024-01-16 13:30:00'), \
('build-019', '/artifacts/build-019/app.tar.gz', 95000000, '2024-01-16 14:00:00'), \
('build-020', '/artifacts/build-020/app.tar.gz', 90222333, '2024-01-16 14:30:00'), \
('build-021', '/artifacts/build-021/app.tar.gz', 85000000, '2024-01-17 10:00:00'), \
('build-022', '/artifacts/build-022/app.tar.gz', 80444555, '2024-01-17 10:30:00'), \
('build-023', '/artifacts/build-023/app.tar.gz', 75000000, '2024-01-17 11:00:00'), \
('build-024', '/artifacts/build-024/app.tar.gz', 70666777, '2024-01-17 11:30:00'), \
('build-025', '/artifacts/build-025/app.tar.gz', 65000000, '2024-01-17 12:00:00'), \
('build-026', '/artifacts/build-026/app.tar.gz', 60888999, '2024-01-17 12:30:00'), \
('build-027', '/artifacts/build-027/app.tar.gz', 55000000, '2024-01-17 13:00:00'), \
('build-028', '/artifacts/build-028/app.tar.gz', 50111222, '2024-01-17 13:30:00'), \
('build-029', '/artifacts/build-029/app.tar.gz', 45000000, '2024-01-17 14:00:00'), \
('build-030', '/artifacts/build-030/app.tar.gz', 40333444, '2024-01-17 14:30:00');"

RUN sqlite3 /home/user/builds/artifacts.db " \
INSERT INTO build_artifacts (build_id, path, size_bytes, created_at) VALUES \
('build-031', '/artifacts/build-031/lib.so', 35000000, '2024-01-18 10:00:00'), \
('build-032', '/artifacts/build-032/lib.so', 30555666, '2024-01-18 10:30:00'), \
('build-033', '/artifacts/build-033/lib.so', 28000000, '2024-01-18 11:00:00'), \
('build-034', '/artifacts/build-034/lib.so', 26777888, '2024-01-18 11:30:00'), \
('build-035', '/artifacts/build-035/lib.so', 25000000, '2024-01-18 12:00:00'), \
('build-036', '/artifacts/build-036/lib.so', 23999111, '2024-01-18 12:30:00'), \
('build-037', '/artifacts/build-037/lib.so', 22000000, '2024-01-18 13:00:00'), \
('build-038', '/artifacts/build-038/lib.so', 20222333, '2024-01-18 13:30:00'), \
('build-039', '/artifacts/build-039/lib.so', 19000000, '2024-01-18 14:00:00'), \
('build-040', '/artifacts/build-040/lib.so', 18444555, '2024-01-18 14:30:00'), \
('build-041', '/artifacts/build-041/debug.log', 17000000, '2024-01-19 10:00:00'), \
('build-042', '/artifacts/build-042/debug.log', 16666777, '2024-01-19 10:30:00'), \
('build-043', '/artifacts/build-043/debug.log', 15000000, '2024-01-19 11:00:00'), \
('build-044', '/artifacts/build-044/debug.log', 14888999, '2024-01-19 11:30:00'), \
('build-045', '/artifacts/build-045/debug.log', 13000000, '2024-01-19 12:00:00'), \
('build-046', '/artifacts/build-046/debug.log', 12111222, '2024-01-19 12:30:00'), \
('build-047', '/artifacts/build-047/debug.log', 11000000, '2024-01-19 13:00:00'), \
('build-048', '/artifacts/build-048/debug.log', 10333444, '2024-01-19 13:30:00'), \
('build-049', '/artifacts/build-049/debug.log', 9500000, '2024-01-19 14:00:00'), \
('build-050', '/artifacts/build-050/debug.log', 9000000, '2024-01-19 14:30:00');"

RUN sqlite3 /home/user/builds/artifacts.db " \
INSERT INTO build_artifacts (build_id, path, size_bytes, created_at) VALUES \
('build-051', '/artifacts/build-051/test-results.xml', 8500000, '2024-01-20 10:00:00'), \
('build-052', '/artifacts/build-052/test-results.xml', 8000000, '2024-01-20 10:30:00'), \
('build-053', '/artifacts/build-053/test-results.xml', 7500000, '2024-01-20 11:00:00'), \
('build-054', '/artifacts/build-054/test-results.xml', 7000000, '2024-01-20 11:30:00'), \
('build-055', '/artifacts/build-055/test-results.xml', 6500000, '2024-01-20 12:00:00'), \
('build-056', '/artifacts/build-056/test-results.xml', 6000000, '2024-01-20 12:30:00'), \
('build-057', '/artifacts/build-057/test-results.xml', 5500000, '2024-01-20 13:00:00'), \
('build-058', '/artifacts/build-058/test-results.xml', 5000000, '2024-01-20 13:30:00'), \
('build-059', '/artifacts/build-059/test-results.xml', 4500000, '2024-01-20 14:00:00'), \
('build-060', '/artifacts/build-060/test-results.xml', 4000000, '2024-01-20 14:30:00'), \
('build-061', '/artifacts/build-061/coverage.html', 3500000, '2024-01-21 10:00:00'), \
('build-062', '/artifacts/build-062/coverage.html', 3000000, '2024-01-21 10:30:00'), \
('build-063', '/artifacts/build-063/coverage.html', 2500000, '2024-01-21 11:00:00'), \
('build-064', '/artifacts/build-064/coverage.html', 2000000, '2024-01-21 11:30:00'), \
('build-065', '/artifacts/build-065/coverage.html', 1500000, '2024-01-21 12:00:00'), \
('build-066', '/artifacts/build-066/coverage.html', 1000000, '2024-01-21 12:30:00'), \
('build-067', '/artifacts/build-067/coverage.html', 950000, '2024-01-21 13:00:00'), \
('build-068', '/artifacts/build-068/coverage.html', 900000, '2024-01-21 13:30:00'), \
('build-069', '/artifacts/build-069/coverage.html', 850000, '2024-01-21 14:00:00'), \
('build-070', '/artifacts/build-070/coverage.html', 800000, '2024-01-21 14:30:00');"

RUN sqlite3 /home/user/builds/artifacts.db " \
INSERT INTO build_artifacts (build_id, path, size_bytes, created_at) VALUES \
('build-071', '/artifacts/build-071/docs.zip', 750000, '2024-01-22 10:00:00'), \
('build-072', '/artifacts/build-072/docs.zip', 700000, '2024-01-22 10:30:00'), \
('build-073', '/artifacts/build-073/docs.zip', 650000, '2024-01-22 11:00:00'), \
('build-074', '/artifacts/build-074/docs.zip', 600000, '2024-01-22 11:30:00'), \
('build-075', '/artifacts/build-075/docs.zip', 550000, '2024-01-22 12:00:00'), \
('build-076', '/artifacts/build-076/docs.zip', 500000, '2024-01-22 12:30:00'), \
('build-077', '/artifacts/build-077/docs.zip', 450000, '2024-01-22 13:00:00'), \
('build-078', '/artifacts/build-078/docs.zip', 400000, '2024-01-22 13:30:00'), \
('build-079', '/artifacts/build-079/docs.zip', 350000, '2024-01-22 14:00:00'), \
('build-080', '/artifacts/build-080/docs.zip', 300000, '2024-01-22 14:30:00'), \
('build-081', '/artifacts/build-081/metrics.json', 250000, '2024-01-23 10:00:00'), \
('build-082', '/artifacts/build-082/metrics.json', 200000, '2024-01-23 10:30:00'), \
('build-083', '/artifacts/build-083/metrics.json', 150000, '2024-01-23 11:00:00'), \
('build-084', '/artifacts/build-084/metrics.json', 100000, '2024-01-23 11:30:00'), \
('build-085', '/artifacts/build-085/metrics.json', 95000, '2024-01-23 12:00:00'), \
('build-086', '/artifacts/build-086/metrics.json', 90000, '2024-01-23 12:30:00'), \
('build-087', '/artifacts/build-087/metrics.json', 85000, '2024-01-23 13:00:00'), \
('build-088', '/artifacts/build-088/metrics.json', 80000, '2024-01-23 13:30:00'), \
('build-089', '/artifacts/build-089/metrics.json', 75000, '2024-01-23 14:00:00'), \
('build-090', '/artifacts/build-090/metrics.json', 70000, '2024-01-23 14:30:00');"

RUN sqlite3 /home/user/builds/artifacts.db " \
INSERT INTO build_artifacts (build_id, path, size_bytes, created_at) VALUES \
('build-091', '/artifacts/build-091/config.yaml', 65000, '2024-01-24 10:00:00'), \
('build-092', '/artifacts/build-092/config.yaml', 60000, '2024-01-24 10:30:00'), \
('build-093', '/artifacts/build-093/config.yaml', 55000, '2024-01-24 11:00:00'), \
('build-094', '/artifacts/build-094/config.yaml', 50000, '2024-01-24 11:30:00'), \
('build-095', '/artifacts/build-095/config.yaml', 45000, '2024-01-24 12:00:00'), \
('build-096', '/artifacts/build-096/config.yaml', 40000, '2024-01-24 12:30:00'), \
('build-097', '/artifacts/build-097/config.yaml', 35000, '2024-01-24 13:00:00'), \
('build-098', '/artifacts/build-098/config.yaml', 30000, '2024-01-24 13:30:00'), \
('build-099', '/artifacts/build-099/config.yaml', 25000, '2024-01-24 14:00:00'), \
('build-100', '/artifacts/build-100/config.yaml', 20000, '2024-01-24 14:30:00'), \
('build-101', '/artifacts/build-101/manifest.txt', 18000, '2024-01-25 10:00:00'), \
('build-102', '/artifacts/build-102/manifest.txt', 16000, '2024-01-25 10:30:00'), \
('build-103', '/artifacts/build-103/manifest.txt', 14000, '2024-01-25 11:00:00'), \
('build-104', '/artifacts/build-104/manifest.txt', 12000, '2024-01-25 11:30:00'), \
('build-105', '/artifacts/build-105/manifest.txt', 10000, '2024-01-25 12:00:00'), \
('build-106', '/artifacts/build-106/manifest.txt', 9000, '2024-01-25 12:30:00'), \
('build-107', '/artifacts/build-107/manifest.txt', 8000, '2024-01-25 13:00:00'), \
('build-108', '/artifacts/build-108/manifest.txt', 7000, '2024-01-25 13:30:00'), \
('build-109', '/artifacts/build-109/manifest.txt', 6000, '2024-01-25 14:00:00'), \
('build-110', '/artifacts/build-110/manifest.txt', 5000, '2024-01-25 14:30:00');"

RUN sqlite3 /home/user/builds/artifacts.db " \
INSERT INTO build_artifacts (build_id, path, size_bytes, created_at) VALUES \
('build-111', '/artifacts/build-111/checksum.md5', 4500, '2024-01-26 10:00:00'), \
('build-112', '/artifacts/build-112/checksum.md5', 4000, '2024-01-26 10:30:00'), \
('build-113', '/artifacts/build-113/checksum.md5', 3500, '2024-01-26 11:00:00'), \
('build-114', '/artifacts/build-114/checksum.md5', 3000, '2024-01-26 11:30:00'), \
('build-115', '/artifacts/build-115/checksum.md5', 2500, '2024-01-26 12:00:00'), \
('build-116', '/artifacts/build-116/checksum.md5', 2000, '2024-01-26 12:30:00'), \
('build-117', '/artifacts/build-117/checksum.md5', 1800, '2024-01-26 13:00:00'), \
('build-118', '/artifacts/build-118/checksum.md5', 1600, '2024-01-26 13:30:00'), \
('build-119', '/artifacts/build-119/checksum.md5', 1400, '2024-01-26 14:00:00'), \
('build-120', '/artifacts/build-120/checksum.md5', 1200, '2024-01-26 14:30:00'), \
('build-121', '/artifacts/build-121/readme.txt', 1100, '2024-01-27 10:00:00'), \
('build-122', '/artifacts/build-122/readme.txt', 1050, '2024-01-27 10:30:00'), \
('build-123', '/artifacts/build-123/readme.txt', 1024, '2024-01-27 11:00:00'), \
('build-124', '/artifacts/build-124/readme.txt', 1000, '2024-01-27 11:30:00'), \
('build-125', '/artifacts/build-125/readme.txt', 980, '2024-01-27 12:00:00'), \
('build-126', '/artifacts/build-126/readme.txt', 960, '2024-01-27 12:30:00'), \
('build-127', '/artifacts/build-127/readme.txt', 940, '2024-01-27 13:00:00'), \
('build-128', '/artifacts/build-128/readme.txt', 920, '2024-01-27 13:30:00'), \
('build-129', '/artifacts/build-129/readme.txt', 900, '2024-01-27 14:00:00'), \
('build-130', '/artifacts/build-130/readme.txt', 880, '2024-01-27 14:30:00');"

RUN sqlite3 /home/user/builds/artifacts.db " \
INSERT INTO build_artifacts (build_id, path, size_bytes, created_at) VALUES \
('build-131', '/artifacts/build-131/version.txt', 860, '2024-01-28 10:00:00'), \
('build-132', '/artifacts/build-132/version.txt', 840, '2024-01-28 10:30:00'), \
('build-133', '/artifacts/build-133/version.txt', 820, '2024-01-28 11:00:00'), \
('build-134', '/artifacts/build-134/version.txt', 800, '2024-01-28 11:30:00'), \
('build-135', '/artifacts/build-135/version.txt', 780, '2024-01-28 12:00:00'), \
('build-136', '/artifacts/build-136/version.txt', 760, '2024-01-28 12:30:00'), \
('build-137', '/artifacts/build-137/version.txt', 740, '2024-01-28 13:00:00'), \
('build-138', '/artifacts/build-138/version.txt', 720, '2024-01-28 13:30:00'), \
('build-139', '/artifacts/build-139/version.txt', 700, '2024-01-28 14:00:00'), \
('build-140', '/artifacts/build-140/version.txt', 680, '2024-01-28 14:30:00'), \
('build-141', '/artifacts/build-141/license.txt', 660, '2024-01-29 10:00:00'), \
('build-142', '/artifacts/build-142/license.txt', 640, '2024-01-29 10:30:00'), \
('build-143', '/artifacts/build-143/license.txt', 620, '2024-01-29 11:00:00'), \
('build-144', '/artifacts/build-144/license.txt', 600, '2024-01-29 11:30:00'), \
('build-145', '/artifacts/build-145/license.txt', 580, '2024-01-29 12:00:00'), \
('build-146', '/artifacts/build-146/license.txt', 560, '2024-01-29 12:30:00'), \
('build-147', '/artifacts/build-147/license.txt', 540, '2024-01-29 13:00:00'), \
('build-148', '/artifacts/build-148/license.txt', 520, '2024-01-29 13:30:00'), \
('build-149', '/artifacts/build-149/license.txt', 500, '2024-01-29 14:00:00'), \
('build-150', '/artifacts/build-150/license.txt', 480, '2024-01-29 14:30:00');"

RUN chmod 0644 /home/user/builds/artifacts.db

WORKDIR /home/user

CMD ["/bin/bash"]
