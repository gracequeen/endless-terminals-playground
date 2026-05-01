FROM ubuntu:22.04

RUN apt-get update && apt-get install -y python3 python3-pip && pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/android/ndk-r26b/toolchains && chmod -R 0777 /home/user/android

RUN touch /home/user/android/ndk-r26b/ndk-build && chmod +x /home/user/android/ndk-r26b/ndk-build

RUN cat <<EOF > /home/user/android/ndk-r26b/source.properties
Pkg.Desc = Android NDK
Pkg.Revision = 26.1.10909125
EOF

RUN chmod 0644 /home/user/android/ndk-r26b/source.properties

RUN touch /home/user/android/ndk-r26b/toolchains/.placeholder

RUN chmod -R 0777 /home/user/android

RUN useradd -m -d /home/user -s /bin/bash user && chown -R user:user /home/user

USER user
WORKDIR /home/user
