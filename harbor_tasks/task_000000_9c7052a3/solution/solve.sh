#!/bin/bash
# Auto-generated solve script
set -e

mkdir -p /home/user/docs && cat > /home/user/docs/Makefile << 'EOF'
SRC_DIR := src
BUILD_DIR := build

MD_FILES := $(wildcard $(SRC_DIR)/*.md)
HTML_FILES := $(patsubst $(SRC_DIR)/%.md,$(BUILD_DIR)/%.html,$(MD_FILES))

html: $(HTML_FILES)

$(BUILD_DIR)/%.html: $(SRC_DIR)/%.md | $(BUILD_DIR)
	pandoc $< -o $@

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

.PHONY: html
EOF
cat /home/user/docs/Makefile
