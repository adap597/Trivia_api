import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from models import setup_db, Question, Category
import random


# See https://github.com/udacity/nd0044-c2-API-Development-and-Documentation-exercises

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    # CORS(app)
    CORS(app, resources={"/": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type, Authorization, true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    # retrieve all categories
    @app.route("/categories", methods=["GET"])
    def retrieve_categories():
        try:
            categories = Category.query.order_by(Category.id).all()

            return jsonify(
                {
                    "success": True,
                    "categories": {
                        category.id: category.type for category in categories
                    },
                }
            )
        except:
            if len(categories) == 0:
                abort(404)

    # retrieve paginated questions, 10 per page
    @app.route("/questions", methods=["GET"])
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        categories = Category.query.order_by(Category.type).all()
        try:
            if len(current_questions) == 0:
                abort(404)

            else:
                return jsonify(
                    {
                        "success": True,
                        "questions": current_questions,
                        "total_questions": len(selection),
                        "categories": {
                            category.id: category.type for category in categories
                        },
                        "current_category": None,
                    }
                )
        except:
            abort(404)

    # delete question
    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "questions": current_questions,
                    "total_questions": len(Question.query.all()),
                }
            )

        except:
            abort(422)

    # create new question
    @app.route("/questions", methods=["POST"])
    def create_question():
        body = request.get_json()

        new_question = body.get("question", None)
        new_answer = body.get("answer", None)
        new_difficulty = body.get("difficulty", None)
        new_category = body.get("category", None)

        try:
            # See https://pythonexamples.org/python-if-not/
            if not (
                "question" in body
                or "answer" in body
                or "difficulty" in body
                or "category" in body
            ):
                abort(422)

            else:
                question = Question(
                    question=new_question,
                    answer=new_answer,
                    difficulty=new_difficulty,
                    category=new_category,
                )
                question.insert()

                return jsonify({"success": True, "created": question.id})
        except:
            abort(422)

    # search questions
    @app.route("/questions/search", methods=["GET", "POST"])
    def search_questions():
        body = request.get_json()
        search_term = body.get("searchTerm", None)
        try:
            if search_term:
                selection = Question.query.filter(
                    Question.question.ilike(f"%{search_term}%")
                ).all()

                return jsonify(
                    {
                        "success": True,
                        "questions": [question.format() for question in selection],
                        "total_questions": len(selection),
                        "current_category": None,
                    }
                )
        except:
            abort(404)

    # get questions by category
    @app.route("/categories/<int:category_id>/questions", methods=["GET"])
    def get_questions_by_category(category_id):
        try:
            questions = Question.query.filter(Question.category == category_id).all()

            return jsonify(
                {
                    "success": True,
                    "questions": [question.format() for question in questions],
                    "total_questions": len(questions),
                    "current_category": category_id,
                }
            )
        except:
            abort(404)

    # play quizzes
    @app.route("/quizzes", methods=["POST"])
    def get_quizzes():
        try:

            data = request.get_json()
            previous_questions = data.get("previous_questions")
            category = data.get("quiz_category")
            category_id = category["id"]

            # See https://docs.sqlalchemy.org/en/14/core/sqlelement.html#sqlalchemy.sql.operators.ColumnOperators.notin_
            if category_id == 0:
                quiz_questions = Question.query.filter(
                    Question.id.notin_((previous_questions))
                ).all()

            else:
                quiz_questions = (
                    Question.query.filter_by(category=category_id)
                    .filter(Question.id.notin_((previous_questions)))
                    .all()
                )

            if quiz_questions:
                # See https://docs.python.org/3/library/random.html
                quiz_questions = quiz_questions[
                    random.randrange(0, len(quiz_questions) - 1)
                ]

            return jsonify({"success": True, "question": quiz_questions.format()})
        except:
            abort(422)

    # error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(500)
    def internal_server_error(error):
        print(error)
        return (
            jsonify(
                {"success": False, "error": 500, "message": "internal server error"}
            ),
            500,
        )

    return app
