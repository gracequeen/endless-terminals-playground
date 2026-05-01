FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/user
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV MAVEN_HOME=/opt/maven
ENV PATH="${MAVEN_HOME}/bin:${PATH}"

RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    curl \
    wget \
    python3 \
    python3-pip \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN wget -q https://archive.apache.org/dist/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.tar.gz -O /tmp/maven.tar.gz && \
    tar -xzf /tmp/maven.tar.gz -C /opt && \
    mv /opt/apache-maven-3.9.6 /opt/maven && \
    rm /tmp/maven.tar.gz

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/.m2/repository/com/internal/payment-utils/2.3.1 && \
    mkdir -p /home/user/invoice-service/src/main/java/com/example/invoice && \
    mkdir -p /home/user/invoice-service/src/main/resources

RUN cat <<'EOF' > /home/user/.m2/settings.xml
<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.2.0 https://maven.apache.org/xsd/settings-1.2.0.xsd">
  <mirrors>
    <mirror>
      <id>nexus-internal</id>
      <mirrorOf>*</mirrorOf>
      <url>http://localhost:8081/repository/maven-public/</url>
    </mirror>
  </mirrors>
</settings>
EOF

RUN cat <<'EOF' > /home/user/invoice-service/pom.xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>invoice-service</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <dependencies>
        <dependency>
            <groupId>com.internal</groupId>
            <artifactId>payment-utils</artifactId>
            <version>2.3.1</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-jar-plugin</artifactId>
                <version>3.3.0</version>
            </plugin>
        </plugins>
    </build>
</project>
EOF

RUN cat <<'EOF' > /home/user/.m2/repository/com/internal/payment-utils/2.3.1/payment-utils-2.3.1.pom
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.internal</groupId>
    <artifactId>payment-utils</artifactId>
    <version>2.3.1</version>
    <packaging>jar</packaging>
</project>
EOF

RUN cat <<'EOF' > /home/user/.m2/repository/com/internal/payment-utils/2.3.1/_remote.repositories
payment-utils-2.3.1.pom>nexus-internal=
payment-utils-2.3.1.jar>nexus-internal=
EOF

RUN mkdir -p /tmp/payment-utils-jar/com/internal/payment && \
    cat <<'EOF' > /tmp/payment-utils-jar/com/internal/payment/PaymentUtils.java
package com.internal.payment;

public class PaymentUtils {
    public static String getVersion() {
        return "2.3.1";
    }

    public static double calculateTax(double amount, double rate) {
        return amount * rate;
    }
}
EOF

RUN cd /tmp/payment-utils-jar && \
    javac com/internal/payment/PaymentUtils.java && \
    jar cf /home/user/.m2/repository/com/internal/payment-utils/2.3.1/payment-utils-2.3.1.jar com/internal/payment/PaymentUtils.class && \
    rm -rf /tmp/payment-utils-jar

RUN cat <<'EOF' > /home/user/invoice-service/src/main/java/com/example/invoice/InvoiceService.java
package com.example.invoice;

import com.internal.payment.PaymentUtils;

public class InvoiceService {

    public double calculateInvoiceTotal(double subtotal, double taxRate) {
        double tax = PaymentUtils.calculateTax(subtotal, taxRate);
        return subtotal + tax;
    }

    public String getPaymentUtilsVersion() {
        return PaymentUtils.getVersion();
    }

    public static void main(String[] args) {
        InvoiceService service = new InvoiceService();
        System.out.println("Invoice Service initialized");
        System.out.println("Using Payment Utils version: " + service.getPaymentUtilsVersion());
    }
}
EOF

RUN chown -R 1000:1000 /home/user && \
    chmod -R 0777 /home/user

WORKDIR /home/user

USER 1000

CMD ["/bin/bash"]
