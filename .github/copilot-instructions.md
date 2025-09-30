<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# AI Call System - Copilot Instructions

This is a Django-based AI call handling system with Twilio integration, CRM capabilities, and advanced scheduling features.

## Project Architecture

### Core Components
- **Django REST Framework**: API endpoints for all functionality
- **Celery**: Background task processing for calls and AI operations
- **Twilio**: Telephony services for inbound/outbound calls
- **OpenAI**: AI conversation handling and processing
- **Redis**: Message broker and caching
- **PostgreSQL**: Primary database (SQLite for development)

### App Structure
- `calls/`: Call management, Twilio integration, queue processing
- `crm/`: Contact management, notes, tags, import/export
- `ai_integration/`: OpenAI integration, conversation management, analytics
- `scheduling/`: Campaign management, bulk operations, scheduling

## Development Guidelines

### Code Style
- Follow Django best practices and PEP 8
- Use UUID primary keys for all models
- Include comprehensive logging
- Add docstrings to all classes and methods
- Use type hints where applicable

### Model Design
- All models should have `created_at` and `updated_at` timestamps
- Use JSONField for flexible data storage
- Include proper database indexes for performance
- Use foreign keys with appropriate on_delete behaviors

### API Design
- Use Django REST Framework ViewSets for CRUD operations
- Include proper error handling and status codes
- Add filtering, searching, and pagination
- Use serializers for data validation and transformation

### Task Processing
- Use Celery shared_task decorator for background tasks
- Include retry logic for critical operations
- Add comprehensive error handling and logging
- Process operations asynchronously when possible

### Twilio Integration
- Validate webhook signatures in production
- Handle all Twilio webhook events appropriately
- Include proper TwiML response generation
- Store call metadata for analytics

### AI Integration
- Support multiple AI providers through abstraction
- Include conversation context and history
- Track token usage and costs
- Implement proper error handling for API failures

## Common Patterns

### Error Handling
```python
try:
    # Operation
    result = perform_operation()
    logger.info(f"Operation successful: {result}")
    return {'success': True, 'data': result}
except SpecificException as e:
    logger.error(f"Operation failed: {str(e)}")
    return {'success': False, 'error': str(e)}
```

### Background Tasks
```python
@shared_task(bind=True, max_retries=3)
def process_task(self, task_data):
    try:
        # Process task
        result = process_data(task_data)
        return result
    except Exception as e:
        if self.request.retries < self.max_retries:
            self.retry(countdown=60)
        logger.error(f"Task failed: {str(e)}")
        raise
```

### API Responses
```python
return Response({
    'success': True,
    'data': serialized_data,
    'message': 'Operation completed successfully'
}, status=status.HTTP_200_OK)
```

## Security Considerations
- Validate all Twilio webhooks using signature verification
- Use proper authentication for all API endpoints
- Sanitize user inputs and prevent injection attacks
- Implement rate limiting for API endpoints
- Secure storage of API keys and sensitive data

## Testing Recommendations
- Write unit tests for all models and services
- Create integration tests for API endpoints
- Mock external services (Twilio, OpenAI) in tests
- Test webhook handling with sample payloads
- Include performance tests for bulk operations

## Deployment Notes
- Use environment variables for all configuration
- Set up proper logging and monitoring
- Configure Celery with appropriate concurrency
- Set up database connection pooling
- Use reverse proxy for static file serving
