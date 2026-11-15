# Network Monitoring and Performance Analysis System

CCS 234 (Networking & Communications) final project, West Visayas State University.

A Python desktop app that discovers devices on a local network, tests connectivity, analyzes performance, gives security recommendations and generates reports.

## Requirements

- Python 3.10 or newer
- Windows 10/11 (primary), Linux or macOS (best effort)
- Windows only: Npcap (https://npcap.com/) for ARP scanning and packet capture (install with "WinPcap API-compatible mode")
- Administrator rights for ARP scanning and packet capture; without them the app falls back to a ping sweep and the system ARP table

## Setup

python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/macOS
pip install -r requirements.txt
copy .env.example .env          # Windows (use cp on Linux/macOS), then edit values

## Run

python src/main.py

## Features

Core: network discovery, connectivity testing, network statistics, report generator, security recommendations.

Bonus: GUI, dashboard charts and live latency graph, real-time monitoring, PDF export, email notifications, port scanner, packet capture, cloud storage and scan history, MAC vendor lookup, new-device alerts, network health score.

## Project structure

src/
  main.py        entry point
  gui/           main window and feature tabs
  core/          discovery, ping, stats, monitoring, port scan, capture, security
  reports/       text/CSV reports and PDF export
  services/      database and email notifications
  utils/         shared helpers and config

## Team

- Person 1: scaffold, GUI, integration, discovery, MAC vendor, new-device alerts, database and history
- Person 2: ping, statistics, real-time monitoring, charts, health score, packet capture
- Person 3: reports, PDF export, email, security recommendations, port scanner
