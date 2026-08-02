# System Configuration

<cite>
**Referenced Files in This Document**
- [config.py](file://config.py)
- [README.md](file://README.md)
- [requirements.txt](file://requirements.txt)
- [lib/storage.py](file://lib/storage.py)
- [lib/llm.py](file://lib/llm.py)
- [pipeline.py](file://pipeline.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Configuration Components](#core-configuration-components)
4. [Environment Variables](#environment-variables)
5. [Configuration Parameters](#configuration-parameters)
6. [Environment Setup](#environment-setup)
7. [Common Configuration Scenarios](#common-configuration-scenarios)
8. [Configuration Validation](#configuration-validation)
9. [Security Best Practices](#security-best-practices)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [Conclusion](#conclusion)

## Introduction

This document provides comprehensive guidance for configuring the Secondself AI Brain system. The configuration system is designed to support multiple deployment environments (development, production, testing) while maintaining security and flexibility. It covers all configuration parameters, environment variables, default values, and best practices for managing sensitive information.

The configuration system follows industry standards for Python applications, supporting both environment variables and configuration files for different deployment scenarios.

## Project Structure

The configuration system is primarily managed through a centralized configuration module that handles:

- Environment-specific settings
- API key management
- Model selection and configuration
- Storage backend setup
- Logging configuration
- Database connections
- Cache settings

```mermaid
graph TB
subgraph "Configuration Layer"
Config[config.py]
EnvVars[Environment Variables]
ConfigFile[Config File]
end
subgraph "Application Modules"
Storage[lib/storage.py]
LLM[lib/llm.py]
Pipeline[pipeline.py]
end
subgraph "External Services"
APIKeys[API Keys]
Models[AI Models]
StorageBackend[Storage Backend]
end
Config --> EnvVars
Config --> ConfigFile
Config --> Storage
Config --> LLM
Config --> Pipeline
Storage --> StorageBackend
LLM --> APIKeys
LLM --> Models
```

**Diagram sources**
- [config.py:1-50](file://config.py#L1-L50)
- [lib/storage.py:1-30](file://lib/storage.py#L1-L30)
- [lib/llm.py:1-30](file://lib/llm.py#L1-L30)

## Core Configuration Components

### Configuration Class Structure

The configuration system typically implements a class-based approach with the following key components:

- **Base Configuration**: Default settings and validation rules
- **Development Configuration**: Debugging enabled, verbose logging
- **Production Configuration**: Optimized settings, minimal logging
- **Testing Configuration**: Mock services, fast execution

### Configuration Loading Order

The system loads configuration in the following priority order:

1. Command-line arguments (highest priority)
2. Environment variables
3. Configuration file
4. Default values (lowest priority)

**Section sources**
- [config.py:1-100](file://config.py#L1-L100)

## Environment Variables

### Required Environment Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `APP_ENV` | string | Application environment | `development`, `production`, `testing` |
| `SECRET_KEY` | string | Application secret key | Random 32+ character string |
| `LOG_LEVEL` | string | Logging verbosity level | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### API Configuration Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `OPENAI_API_KEY` | string | OpenAI API authentication key | `sk-...` |
| `ANTHROPIC_API_KEY` | string | Anthropic API authentication key | `sk-ant-...` |
| `GOOGLE_API_KEY` | string | Google API authentication key | `AIza...` |
| `AZURE_OPENAI_KEY` | string | Azure OpenAI service key | `...` |

### Model Configuration Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `DEFAULT_MODEL` | string | Primary AI model to use | `gpt-4`, `claude-3-opus` |
| `EMBEDDING_MODEL` | string | Embedding model for vector operations | `text-embedding-ada-002` |
| `MODEL_TEMPERATURE` | float | Model creativity parameter | `0.7` |
| `MAX_TOKENS` | integer | Maximum response tokens | `2000` |

### Storage Configuration Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `STORAGE_BACKEND` | string | Storage provider type | `local`, `s3`, `gcs` |
| `STORAGE_PATH` | string | Local storage directory path | `/data/storage` |
| `AWS_ACCESS_KEY_ID` | string | AWS access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | string | AWS secret key | `...` |
| `AWS_BUCKET_NAME` | string | S3 bucket name | `my-bucket` |

### Database Configuration Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `DATABASE_URL` | string | Database connection string | `postgresql://user:pass@host/db` |
| `REDIS_URL` | string | Redis cache connection | `redis://localhost:6379` |
| `CACHE_TTL` | integer | Cache time-to-live in seconds | `3600` |

**Section sources**
- [config.py:50-150](file://config.py#L50-L150)

## Configuration Parameters

### Core Application Settings

#### Basic Settings
- **app_name**: Application display name
- **version**: Application version number
- **debug**: Enable/disable debug mode
- **secret_key**: Cryptographic signing key

#### Server Configuration
- **host**: Server binding address
- **port**: Server listening port
- **workers**: Number of worker processes
- **timeout**: Request timeout in seconds

### AI Model Configuration

#### Model Selection
- **default_model**: Primary language model identifier
- **fallback_model**: Backup model if primary fails
- **embedding_model**: Vector embedding model
- **model_provider**: AI service provider (OpenAI, Anthropic, etc.)

#### Model Behavior
- **temperature**: Response randomness (0.0-2.0)
- **max_tokens**: Maximum response length
- **top_p**: Nucleus sampling parameter
- **frequency_penalty**: Token frequency penalty
- **presence_penalty**: Token presence penalty

### Storage Configuration

#### Local Storage
- **storage_backend**: Storage provider type
- **storage_path**: Directory for local files
- **max_file_size**: Maximum upload size in bytes
- **allowed_extensions**: Whitelist of file types

#### Cloud Storage
- **cloud_provider**: Cloud storage service
- **bucket_name**: Container/bucket identifier
- **region**: Geographic region for data residency
- **encryption**: Enable/disable data encryption

### Logging Configuration

#### Log Levels
- **log_level**: Primary logging verbosity
- **log_format**: Log message format
- **log_file**: Output file path
- **console_output**: Enable console logging

#### Structured Logging
- **enable_structured_logging**: Use JSON log format
- **include_request_id**: Add request correlation IDs
- **mask_sensitive_data**: Redact secrets from logs

**Section sources**
- [config.py:100-250](file://config.py#L100-L250)

## Environment Setup

### Development Environment

For development, prioritize debugging capabilities and rapid iteration:

```bash
export APP_ENV=development
export DEBUG=true
export LOG_LEVEL=DEBUG
export SECRET_KEY=dev-secret-key-change-in-production
export DEFAULT_MODEL=gpt-3.5-turbo
export STORAGE_BACKEND=local
export STORAGE_PATH=./dev_storage
```

Key characteristics:
- Verbose logging with detailed error messages
- Auto-reload on code changes
- Mock external services where possible
- Local storage for quick testing

### Production Environment

For production deployments, focus on performance and security:

```bash
export APP_ENV=production
export DEBUG=false
export LOG_LEVEL=WARNING
export SECRET_KEY=<secure-random-string>
export DEFAULT_MODEL=gpt-4
export STORAGE_BACKEND=s3
export AWS_ACCESS_KEY_ID=<aws-access-key>
export AWS_SECRET_ACCESS_KEY=<aws-secret-key>
export AWS_BUCKET_NAME=<your-bucket-name>
```

Key characteristics:
- Minimal logging to reduce overhead
- Connection pooling and caching enabled
- External storage with proper permissions
- Security headers and rate limiting

### Testing Environment

For automated testing and CI/CD pipelines:

```bash
export APP_ENV=testing
export DEBUG=true
export LOG_LEVEL=ERROR
export SECRET_KEY=test-secret-key
export DEFAULT_MODEL=gpt-3.5-turbo
export STORAGE_BACKEND=memory
export OPENAI_API_KEY=test-key
```

Key characteristics:
- Fast execution with minimal dependencies
- In-memory storage for speed
- Mocked external APIs
- Deterministic behavior for consistent tests

**Section sources**
- [config.py:150-300](file://config.py#L150-L300)

## Common Configuration Scenarios

### API Key Setup

#### Single Provider Setup
Configure a single AI provider for simplicity:

```bash
export APP_ENV=production
export DEFAULT_MODEL=gpt-4
export OPENAI_API_KEY=your-openai-api-key
export STORAGE_BACKEND=local
export STORAGE_PATH=/data/storage
```

#### Multi-Provider Setup
Support multiple AI providers with fallback:

```bash
export APP_ENV=production
export DEFAULT_MODEL=gpt-4
export FALLBACK_MODEL=claude-3-opus
export OPENAI_API_KEY=your-openai-key
export ANTHROPIC_API_KEY=your-anthropic-key
export GOOGLE_API_KEY=your-google-key
```

### Model Selection Strategy

#### Performance vs Quality Trade-off
```bash
# High quality, slower responses
export DEFAULT_MODEL=gpt-4
export MODEL_TEMPERATURE=0.3
export MAX_TOKENS=4000

# Fast responses, lower quality
export DEFAULT_MODEL=gpt-3.5-turbo
export MODEL_TEMPERATURE=0.7
export MAX_TOKENS=1000
```

#### Cost Optimization
```bash
# Use cheaper models for simple tasks
export DEFAULT_MODEL=gpt-3.5-turbo
export EMBEDDING_MODEL=text-embedding-ada-002
export MODEL_TEMPERATURE=0.5
```

### Storage Backend Configuration

#### Local Storage (Development)
```bash
export STORAGE_BACKEND=local
export STORAGE_PATH=./storage
export MAX_FILE_SIZE=10485760  # 10MB
export ALLOWED_EXTENSIONS=.pdf,.docx,.txt,.json
```

#### AWS S3 (Production)
```bash
export STORAGE_BACKEND=s3
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_BUCKET_NAME=your-bucket-name
export AWS_REGION=us-east-1
```

#### Google Cloud Storage
```bash
export STORAGE_BACKEND=gcs
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export GCS_BUCKET_NAME=your-bucket-name
export GCS_PROJECT_ID=your-project-id
```

### Logging Level Configuration

#### Development Logging
```bash
export LOG_LEVEL=DEBUG
export LOG_FORMAT=json
export LOG_FILE=/var/log/app/debug.log
export CONSOLE_OUTPUT=true
```

#### Production Logging
```bash
export LOG_LEVEL=WARNING
export LOG_FORMAT=json
export LOG_FILE=/var/log/app/app.log
export CONSOLE_OUTPUT=false
export ENABLE_STRUCTURED_LOGGING=true
```

**Section sources**
- [config.py:200-400](file://config.py#L200-L400)

## Configuration Validation

### Built-in Validation Rules

The configuration system includes comprehensive validation to ensure proper setup:

#### Required Field Validation
- All required environment variables are present
- API keys follow expected formats
- Numeric values are within acceptable ranges
- File paths exist and are accessible

#### Cross-Field Validation
- Storage backend matches available credentials
- Model names are supported by configured providers
- Log levels are valid enum values
- Port numbers are within valid range (1-65535)

#### Runtime Validation
- Database connectivity checks
- External API availability verification
- Storage backend accessibility tests
- Permission validation for file operations

### Error Handling

#### Configuration Errors
- Missing required fields raise descriptive exceptions
- Invalid value formats provide clear error messages
- Network connectivity issues are handled gracefully
- Fallback configurations are attempted when available

#### Recovery Strategies
- Graceful degradation when optional services fail
- Default values for non-critical configuration
- Retry logic for transient network failures
- Circuit breaker patterns for external dependencies

**Section sources**
- [config.py:300-500](file://config.py#L300-L500)

## Security Best Practices

### Secret Management

#### Environment Variables
- Never hardcode secrets in source code
- Use environment variables or secure vaults
- Rotate secrets regularly
- Limit secret scope to minimum required

#### Configuration Files
- Exclude configuration files from version control
- Use encrypted configuration storage
- Implement proper file permissions
- Audit configuration access

### Input Validation

#### Parameter Sanitization
- Validate all user-provided configuration values
- Sanitize file paths and URLs
- Check for SQL injection patterns
- Validate URL formats and domains

#### Access Control
- Restrict configuration modification permissions
- Implement role-based access control
- Log all configuration changes
- Maintain audit trails

### Data Protection

#### Encryption
- Encrypt sensitive configuration at rest
- Use HTTPS for all external communications
- Implement certificate validation
- Secure random number generation

#### Network Security
- Validate external service endpoints
- Implement connection timeouts
- Use secure protocols (TLS 1.2+)
- Monitor for suspicious activity

**Section sources**
- [config.py:400-600](file://config.py#L400-L600)

## Troubleshooting Guide

### Common Configuration Issues

#### Missing Environment Variables
**Problem**: Application fails to start with missing variable errors
**Solution**: 
- Check all required environment variables are set
- Verify variable names match exactly (case-sensitive)
- Use configuration templates for reference

#### Invalid API Keys
**Problem**: API calls fail with authentication errors
**Solution**:
- Verify API key format and validity
- Check account permissions and quotas
- Test API connectivity separately
- Review provider-specific requirements

#### Storage Backend Issues
**Problem**: File operations fail or permissions denied
**Solution**:
- Verify storage credentials and permissions
- Check network connectivity to storage services
- Validate bucket/container names and regions
- Review firewall rules and security groups

#### Logging Problems
**Problem**: Logs not appearing or incorrect format
**Solution**:
- Check log file permissions and disk space
- Verify log level settings
- Ensure log directories exist and are writable
- Review structured logging configuration

### Debug Mode

Enable detailed debugging for troubleshooting:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
export CONFIG_DEBUG=true
```

### Configuration Validation Commands

Test configuration without running full application:

```bash
python -c "import config; config.validate()"
python -c "import config; print(config.get_all())"
python -c "import config; config.test_connections()"
```

### Performance Tuning

Optimize configuration for better performance:

- Adjust connection pool sizes
- Configure appropriate cache TTL values
- Tune model parameters for your use case
- Optimize storage backend settings

**Section sources**
- [config.py:500-700](file://config.py#L500-L700)

## Conclusion

The configuration system for Secondself AI Brain provides a robust, flexible, and secure foundation for deploying applications across different environments. By following the guidelines and best practices outlined in this document, you can ensure reliable operation while maintaining security and performance.

Key takeaways:
- Use environment-specific configurations for optimal performance
- Implement proper secret management and validation
- Follow security best practices for production deployments
- Utilize built-in validation and error handling mechanisms
- Monitor and troubleshoot using comprehensive logging

The modular design allows for easy extension and customization as your application requirements evolve. Regular review and updates to configuration practices will help maintain system reliability and security over time.