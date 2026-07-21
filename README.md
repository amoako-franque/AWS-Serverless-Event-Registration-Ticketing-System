AWS Serverless Event Registration & Ticketing System
Project Overview

The Event Registration & Ticketing System is a cloud-native, serverless application designed to replace a manual event registration process that relied on Microsoft Forms and Excel spreadsheets. The solution leverages AWS managed services to provide a scalable, secure, and cost-effective REST API for managing events and attendee registrations.

The application enables event organizers to create and manage events while allowing attendees to register online and receive automated confirmation emails. By adopting a serverless architecture, the system eliminates server management, automatically scales with demand, and minimizes operational costs.
Problem

An event management organization was managing growing registration volumes through Microsoft Forms and Excel spreadsheets. This created:

No automated attendee confirmation emails
No real-time visibility into system health or errors
No structured, repeatable deployment process
No way to enforce spend limits or track cost against a free-tier budget

This project replaces that manual workflow with a serverless REST API that scales automatically, confirms registrations by email, tracks its own cost, and deploys through a CI/CD pipeline.

Architecture overview