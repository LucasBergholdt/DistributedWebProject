# DistributedWebProject – Kollektivportalen

This repository contains the final project for the course DM585: Distributed and Web Programming at SDU.
In a three man group we implemented a web platform named "Kollektivportalen" for connecting people looking for a shared housing (seekers) with people offering collective housing (providers).
The goal was to build a realistic prototype of a housing-matching portal where:
- seekers can browse available collectives and maintain a profile
- providers can create and manage collective listings
- users can authenticate and access role-specific functionality

## Architecture Highlights
The project contains the same domain in two architectural styles:

### 1) Monolith (artefact-1)
- Modular Flask app with blueprints and app factory pattern
- Server-rendered templates with role-based navigation and access
- SQLite persistence and image upload handling

## 2) Microservices (artefact-2)
- Service-oriented decomposition with clear boundaries:
  - Frontend (orchestration + UI)
  - Auth (users, sessions, tokens)
  - Collectives (listing domain)
  - Profile (seeker profile domain)
  - Pictures (image storage/retrieval)
- Each service has its own database
- Containerized setup via Docker Compose

## Tech Stack
- Python, Flask, SQLAlchemy
- WTForms, Jinja2, Bootstrap
- PostgreSQL (microservices), SQLite (monolith)
- Docker / Docker Compose
- REST-style service communication

## Takeaways from this project
This project helped me learn about:
- domain-driven decomposition
- authentication/session flows across services
- role-based authorization
- API design and inter-service communication
- containerized local environments
- architectural trade-off analysis (monolith vs microservices)
