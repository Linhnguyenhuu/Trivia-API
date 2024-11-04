import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# pagination
def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
        
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
        
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    # @DONE: Set up CORS. Allow '*' for origins. 
    CORS(app) 
    #CORS(app, resources={r"/api/*": {"origins": "*"}})

    # @DONE: Use the after_request decorator to set Access-Control-Allow
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        response.headers.add("Access-Control-Allow-Origin", "*")
        
        return response

    # @DONE:
    # Create an endpoint to handle GET requests
    # for all available categories.
    @app.route('/categories')
    def get_categories():
        try:
            # get all categories
            categories = Category.query.order_by(Category.id).all()
        
            # not found error
            if len(categories) == 0:
                abort(404)
        except Exception as e:
            raise e
        
        return jsonify ({
            'success': True,
            'categories': {cate.id: cate.type for cate in categories}
        })
        

    # @DONE:
    # Create an endpoint to handle GET requests for questions,
    # including pagination (every 10 questions).
    # This endpoint should return a list of questions,
    # number of total questions, current category, categories.

    # TEST: At this point, when you start the application
    # you should see questions and categories generated,
    # ten questions per page and pagination at the bottom of the screen for three pages.
    # Clicking on the page numbers should update the questions.
    @app.route('/questions')
    def get_questions():
        try:
            # get all questions
            selection = Question.query.order_by(Question.id).all()
        
            # paging 10 questions per page
            current_questions = paginate_questions(request, selection)
        
            # not found error
            if not current_questions:
                abort(404)
        
            # get all categories
            categories = Category.query.all()
        except Exception as e:
            raise e
        
        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': {cate.id: cate.type for cate in categories}
        })
    

    """
    @DONE:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):
        try:
            # get question by id
            question = Question.query.filter_by(id=id).one_or_none()
            
            # Current question does not exist
            if question is None:
                abort(404)
            
            # delete current question
            question.delete()

        except Exception as e:
            raise e
            
        return jsonify({
                'success': True,
                'deleted': id,
                'total_questions': len(Question.query.all())
            })
    

    """
    @DONE:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route("/questions", methods=['POST'])
    def create_new_question():
        # get the input value
        input = request.get_json()
        new_question = input.get('question')
        new_answer = input.get('answer')
        new_category = input.get('category')
        new_difficulty = input.get('difficulty')
        
        # validate input
        if (input, new_question, new_answer, new_category, new_difficulty) is (None or ""):
            abort(422)

        try:
            # insert new question
            question = Question(
                question=new_question,
                answer=new_answer,
                category=new_category,
                difficulty=new_difficulty
                )
            question.insert()

            # binding data
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

        except Exception as e:
            raise e
        
        return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(selection)
            }), 201
    

    """
    @DONE:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        try:
            # get user's input
            body = request.get_json()
            search_input = body.get('searchTerm')
            
            # get all questions have phrase that user searching
            selection = Question.query.filter(Question.question.ilike(f'%{search_input}%')).all()

            if len(selection) != 0:
                search_questions = paginate_questions(request, selection)

                return jsonify({
                    "success": True,
                    "questions": search_questions,
                    "total_questions": len(search_questions)
                })
            else:
                abort(404)
        except Exception as e:
            raise e


    """
    @DONE:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route("/categories/<int:id>/questions")
    def get_questions_by_category(id):      
        try:
            # get category by id
            category = Category.query.filter_by(id=id).one_or_none()
            
            if category is not None:
                # get all questions that match the category
                questions = Question.query.filter_by(category=str(id)).all()
                current_questions = paginate_questions(request, questions)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(questions),
                'current_category': category.type
            })
        except Exception as e:
            raise e
    

    """
    @DONE:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def play_quizzes_game():
        try:
            body = request.get_json()
            current_category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')
            category_id = current_category['id']

            if category_id == 0:
                # if click all, list question will include all categories
                all_questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
            else:
                # if click specified category, display its questions only
                all_questions = Question.query.filter(Question.id.notin_(previous_questions), 
                Question.category == category_id).all()
                
            # choose next question
            next_question = None
            # if list question is not empty, choose the next one
            if (all_questions):
                next_question = random.choice(all_questions)
            # if list question is empty, display player's score
            else:
                return jsonify({
                    'success': True,
                })

            return jsonify({
                'success': True,
                'question': next_question.format()
            })
        except Exception as e:
            raise e
    

    """
    @DONE:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return( 
            jsonify({'success': False, 'error': 404,'message': 'resource not found'}),
            404
        )
    
    @app.errorhandler(422)
    def unprocessed(error):
        return(
            jsonify({'success': False, 'error': 422,'message': 'request cannot be processed'}),
            422
        )

    @app.errorhandler(400)
    def bad_request(error):
        return(
            jsonify({'success': False, 'error': 400,'message': 'bad request'}),
            400
        )

    @app.errorhandler(405)
    def not_allowed(error):
        return(
            jsonify({'success': False, 'error': 405,'message': 'method not alllowed'}),
            405
        )
    
    @app.errorhandler(401)
    def unauthorized(error):
        return(
            jsonify({'success': False, 'error': 401,'message': 'the client must authenticate'}),
            401
        )
    
    @app.errorhandler(408)
    def request_time_out(error):
        return(
            jsonify({'success': False, 'error': 408,'message': 'request time out'}),
            408
        )
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return(
            jsonify({'success': False, 'error': 500,'message': 'internal server error'}),
            500
        )
    
    @app.errorhandler(501)
    def not_implemented(error):
        return(
            jsonify({'success': False, 'error': 501,'message': 'not implement'}),
            501
        )
    
    @app.errorhandler(503)
    def service_unavailable(error):
        return(
            jsonify({'success': False, 'error': 503,'message': 'service unavailable'}),
            503
        )
    
    @app.errorhandler(504)
    def gateway_timeout(error):
        return(
            jsonify({'success': False, 'error': 504,'message': 'gateway timeout'}),
            504
        )
    

    return app
