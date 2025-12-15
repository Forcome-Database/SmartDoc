# Product Overview

## Enterprise IDP Platform (企业级智能文档处理中台)

A high-availability, traceable, intelligent document processing platform that supports automated parsing of single-page and multi-page documents with end-to-end workflow from rule definition, data extraction, human-in-the-loop review, to secure downstream delivery.

## Core Capabilities

- **Document Processing**: Automated OCR and data extraction from PDF and image files (max 20MB, 50 pages)
- **Multi-Engine OCR**: PaddleOCR (primary), Tesseract (fallback)
- **Smart Deduplication**: SHA256-based instant file recognition to save compute resources
- **Intelligent Extraction**: Regex, anchor-based, table extraction, and LLM-enhanced extraction strategies
- **Human Review Workbench**: Visual audit interface with multi-page PDF preview, OCR highlighting, cross-page navigation
- **Secure Webhooks**: HMAC-SHA256 signed push to downstream systems with retry mechanism
- **Rule Engine**: Version control, sandbox testing, hot configuration updates
- **Real-time Dashboard**: Task monitoring, performance analytics, anomaly tracking

## Key Metrics & Goals

- **API Response**: < 200ms (upload)
- **OCR Processing**: < 3s per page
- **Straight-Through Processing (STP)**: > 90% (no human intervention)
- **Instant Recognition**: Cache hit for duplicate files
- **Multi-page Support**: Up to 50 pages with merged text extraction

## User Roles

- **Admin**: Full system configuration and user management
- **Architect**: Rule creation, editing, publishing, sandbox testing
- **Auditor**: Review pending tasks in workbench (no rule modification)
- **Visitor**: API key generation and viewing only
