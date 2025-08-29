"""
Crop Disease Detection System - Chatbot Routes
Routes for handling chatbot interactions and conversations
"""

from flask import Blueprint, request, jsonify, session
from app.models.database import ChatSession
from app.services.chatbot_service import ChatbotService
from app.models.plant_database import PlantDatabase
from app import db
import uuid
import logging
from datetime import datetime, timedelta

# Create blueprint
bp = Blueprint('chatbot', __name__, url_prefix='/chat')

# Initialize services
chatbot_service = ChatbotService()
plant_db = PlantDatabase()

@bp.route('/', methods=['POST'])
def chat():
    """
    Main chatbot endpoint for processing user messages
    
    Expected: JSON with 'message' field and optional 'session_id'
    Returns: JSON with bot response and session information
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'code': 'NO_DATA'
            }), 400
        
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message is required',
                'code': 'EMPTY_MESSAGE'
            }), 400
        
        # Get or create session ID
        session_id = data.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get client information
        user_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        # Process message with chatbot service
        response_data = chatbot_service.process_message(
            user_message=user_message,
            session_id=session_id,
            context=data.get('context', {})
        )
        
        if not response_data['success']:
            return jsonify({
                'success': False,
                'error': response_data['error'],
                'code': 'PROCESSING_ERROR'
            }), 500
        
        bot_response = response_data['response']
        message_type = response_data.get('type', 'general')
        confidence = response_data.get('confidence', 0.8)
        processing_time = response_data.get('processing_time', 0)
        
        # Save conversation to database
        try:
            chat_record = ChatSession(
                session_id=session_id,
                user_message=user_message,
                bot_response=bot_response,
                message_type=message_type,
                confidence_score=confidence,
                response_time=processing_time,
                user_ip=user_ip,
                user_agent=user_agent,
                context_data=str(data.get('context', {}))
            )
            
            db.session.add(chat_record)
            db.session.commit()
            
        except Exception as db_error:
            logging.error(f"Error saving chat session: {db_error}")
            # Continue without failing the request
        
        return jsonify({
            'success': True,
            'response': bot_response,
            'session_id': session_id,
            'message_type': message_type,
            'confidence': confidence,
            'processing_time': processing_time,
            'timestamp': datetime.utcnow().isoformat(),
            'suggestions': response_data.get('suggestions', [])
        }), 200
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error processing message',
            'code': 'INTERNAL_ERROR'
        }), 500

@bp.route('/history/<session_id>')
def get_chat_history(session_id):
    """Get chat history for a specific session"""
    try:
        # Validate session ID format
        try:
            uuid.UUID(session_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID format',
                'code': 'INVALID_SESSION_ID'
            }), 400
        
        # Get pagination parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if limit > 100:
            limit = 100
        
        # Get chat messages for session
        messages = ChatSession.query.filter(
            ChatSession.session_id == session_id
        ).order_by(ChatSession.created_at.asc()).offset(offset).limit(limit).all()
        
        # Convert to response format
        history = []
        for message in messages:
            history.append({
                'id': message.id,
                'user_message': message.user_message,
                'bot_response': message.bot_response,
                'message_type': message.message_type,
                'confidence': message.confidence_score,
                'timestamp': message.created_at.isoformat()
            })
        
        # Get total message count
        total_messages = ChatSession.query.filter(
            ChatSession.session_id == session_id
        ).count()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'history': history,
            'pagination': {
                'total': total_messages,
                'offset': offset,
                'limit': limit,
                'count': len(history)
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting chat history: {e}")
        return jsonify({
            'success': False,
            'error': 'Error retrieving chat history',
            'code': 'HISTORY_ERROR'
        }), 500

@bp.route('/sessions')
def get_recent_sessions():
    """Get recent chat sessions"""
    try:
        # Get sessions from the last 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        sessions = db.session.query(
            ChatSession.session_id,
            db.func.count(ChatSession.id).label('message_count'),
            db.func.max(ChatSession.created_at).label('last_activity'),
            db.func.min(ChatSession.created_at).label('first_activity')
        ).filter(
            ChatSession.created_at >= cutoff_date
        ).group_by(ChatSession.session_id).order_by(
            db.func.max(ChatSession.created_at).desc()
        ).limit(20).all()
        
        sessions_data = []
        for session_id, msg_count, last_activity, first_activity in sessions:
            # Get the most recent message for preview
            recent_message = ChatSession.query.filter(
                ChatSession.session_id == session_id
            ).order_by(ChatSession.created_at.desc()).first()
            
            sessions_data.append({
                'session_id': session_id,
                'message_count': msg_count,
                'last_activity': last_activity.isoformat(),
                'first_activity': first_activity.isoformat(),
                'last_message_preview': recent_message.user_message[:100] + '...' if recent_message and len(recent_message.user_message) > 100 else recent_message.user_message if recent_message else ''
            })
        
        return jsonify({
            'success': True,
            'sessions': sessions_data,
            'total_sessions': len(sessions_data)
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting recent sessions: {e}")
        return jsonify({
            'success': False,
            'error': 'Error retrieving sessions',
            'code': 'SESSIONS_ERROR'
        }), 500

@bp.route('/topics')
def get_popular_topics():
    """Get popular chat topics and message types"""
    try:
        # Get topic distribution from recent messages
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        topics = db.session.query(
            ChatSession.message_type,
            db.func.count(ChatSession.message_type).label('count')
        ).filter(
            ChatSession.created_at >= cutoff_date
        ).group_by(ChatSession.message_type).order_by(
            db.func.count(ChatSession.message_type).desc()
        ).all()
        
        topics_data = [
            {
                'topic': topic,
                'count': count,
                'percentage': round((count / sum(t[1] for t in topics)) * 100, 1) if topics else 0
            }
            for topic, count in topics
        ]
        
        return jsonify({
            'success': True,
            'topics': topics_data,
            'total_messages': sum(topic['count'] for topic in topics_data),
            'period': '7 days'
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting popular topics: {e}")
        return jsonify({
            'success': False,
            'error': 'Error retrieving topics',
            'code': 'TOPICS_ERROR'
        }), 500

@bp.route('/suggestions')
def get_suggestions():
    """Get suggested questions for users"""
    try:
        category = request.args.get('category', 'general')
        
        suggestions = chatbot_service.get_suggested_questions(category)
        
        return jsonify({
            'success': True,
            'category': category,
            'suggestions': suggestions
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting suggestions: {e}")
        return jsonify({
            'success': False,
            'error': 'Error retrieving suggestions',
            'code': 'SUGGESTIONS_ERROR'
        }), 500

@bp.route('/context', methods=['POST'])
def set_conversation_context():
    """Set context for conversation (e.g., based on uploaded image analysis)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'code': 'NO_DATA'
            }), 400
        
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Session ID is required',
                'code': 'NO_SESSION_ID'
            }), 400
        
        context_type = data.get('type', 'general')  # analysis, plant_info, disease_info, general
        context_data = data.get('context', {})
        
        # Store context in chatbot service
        result = chatbot_service.set_session_context(session_id, context_type, context_data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Context set successfully',
                'session_id': session_id,
                'context_type': context_type
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'code': 'CONTEXT_ERROR'
            }), 400
            
    except Exception as e:
        logging.error(f"Error setting context: {e}")
        return jsonify({
            'success': False,
            'error': 'Error setting conversation context',
            'code': 'CONTEXT_SET_ERROR'
        }), 500

@bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback for chatbot responses"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'code': 'NO_DATA'
            }), 400
        
        message_id = data.get('message_id')
        feedback_type = data.get('type')  # helpful, unhelpful, incorrect
        feedback_text = data.get('feedback', '')
        
        if not message_id or not feedback_type:
            return jsonify({
                'success': False,
                'error': 'Message ID and feedback type are required',
                'code': 'MISSING_REQUIRED'
            }), 400
        
        # Find the chat message
        chat_message = ChatSession.query.get(message_id)
        if not chat_message:
            return jsonify({
                'success': False,
                'error': 'Message not found',
                'code': 'MESSAGE_NOT_FOUND'
            }), 404
        
        # Process feedback with chatbot service
        result = chatbot_service.process_feedback(
            message_id=message_id,
            feedback_type=feedback_type,
            feedback_text=feedback_text
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Feedback submitted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'code': 'FEEDBACK_ERROR'
            }), 400
            
    except Exception as e:
        logging.error(f"Error submitting feedback: {e}")
        return jsonify({
            'success': False,
            'error': 'Error submitting feedback',
            'code': 'FEEDBACK_SUBMIT_ERROR'
        }), 500

@bp.route('/clear/<session_id>', methods=['DELETE'])
def clear_chat_history(session_id):
    """Clear chat history for a session"""
    try:
        # Validate session ID
        try:
            uuid.UUID(session_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID format',
                'code': 'INVALID_SESSION_ID'
            }), 400
        
        # Delete all messages for the session
        deleted_count = ChatSession.query.filter(
            ChatSession.session_id == session_id
        ).delete()
        
        db.session.commit()
        
        # Clear context from chatbot service
        chatbot_service.clear_session_context(session_id)
        
        return jsonify({
            'success': True,
            'message': f'Cleared {deleted_count} messages',
            'session_id': session_id
        }), 200
        
    except Exception as e:
        logging.error(f"Error clearing chat history: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Error clearing chat history',
            'code': 'CLEAR_ERROR'
        }), 500

@bp.route('/stats')
def get_chatbot_stats():
    """Get chatbot usage statistics"""
    try:
        # Time periods
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Basic counts
        total_messages = ChatSession.query.count()
        total_sessions = db.session.query(ChatSession.session_id).distinct().count()
        
        # Recent activity
        messages_24h = ChatSession.query.filter(ChatSession.created_at >= day_ago).count()
        messages_7d = ChatSession.query.filter(ChatSession.created_at >= week_ago).count()
        messages_30d = ChatSession.query.filter(ChatSession.created_at >= month_ago).count()
        
        # Active sessions
        active_sessions_24h = db.session.query(ChatSession.session_id).filter(
            ChatSession.created_at >= day_ago
        ).distinct().count()
        
        # Average response time
        avg_response_time = db.session.query(
            db.func.avg(ChatSession.response_time)
        ).scalar() or 0
        
        # Top message types
        top_types = db.session.query(
            ChatSession.message_type,
            db.func.count(ChatSession.message_type).label('count')
        ).group_by(ChatSession.message_type).order_by(
            db.func.count(ChatSession.message_type).desc()
        ).limit(5).all()
        
        stats = {
            'overview': {
                'total_messages': total_messages,
                'total_sessions': total_sessions,
                'average_response_time': round(avg_response_time, 2)
            },
            'activity': {
                'messages_24h': messages_24h,
                'messages_7d': messages_7d,
                'messages_30d': messages_30d,
                'active_sessions_24h': active_sessions_24h
            },
            'popular_topics': [
                {
                    'type': msg_type,
                    'count': count,
                    'percentage': round((count / total_messages) * 100, 1) if total_messages > 0 else 0
                }
                for msg_type, count in top_types
            ],
            'timestamp': now.isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting chatbot stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Error retrieving chatbot statistics',
            'code': 'STATS_ERROR'
        }), 500