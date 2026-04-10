from flask import Flask, jsonify, request, send_from_directory
import mysql.connector
from mysql.connector import Error
import os

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'credirate',
}

app = Flask(__name__, static_folder='static', static_url_path='')


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_all(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def fetch_one(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def get_or_create_user(conn, user_name):
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id FROM users WHERE username = %s', (user_name,))
    user = cursor.fetchone()

    if user is not None:
        cursor.close()
        return user['id']

    cursor.execute(
        '''
        INSERT INTO users (username, is_verified, reputation_score)
        VALUES (%s, 0, 50)
        ''',
        (user_name,)
    )
    user_id = cursor.lastrowid
    cursor.close()
    return user_id


def refresh_user_reputation(conn, user_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        '''
        SELECT
            COUNT(*) AS total_reviews,
            COALESCE(AVG(rating_value), 0) AS average_rating
        FROM ratings
        WHERE user_id = %s
        ''',
        (user_id,)
    )
    stats = cursor.fetchone()

    total_reviews = int(stats['total_reviews'] or 0)
    average_rating = float(stats['average_rating'] or 0)

    score = 40
    if total_reviews >= 2:
        score += 8
    if total_reviews >= 4:
        score += 10
    if total_reviews >= 8:
        score += 12
    if 2.5 <= average_rating <= 4.5:
        score += 8

    score = min(score, 95)
    cursor.execute('UPDATE users SET reputation_score = %s WHERE id = %s', (score, user_id))
    cursor.close()


@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/entities', methods=['GET'])
def get_entities():
    entities = fetch_all('SELECT * FROM vw_trust_scores ORDER BY entity_id ASC')
    return jsonify(entities)


@app.route('/api/entities/<int:entity_id>/details', methods=['GET'])
def get_entity_details(entity_id):
    entity = fetch_one('SELECT * FROM vw_trust_scores WHERE entity_id = %s', (entity_id,))
    if entity is None:
        return jsonify({'error': 'Entity not found'}), 404

    ratings = fetch_all(
        '''
        SELECT
            rating_id, user_id, username, is_verified, reputation_score,
            rating_value, review_text, created_at, age_days,
            recency_factor, recency_bucket, user_reliability_factor,
            reputation_factor, verification_bonus, total_reviews_by_user,
            prior_reviews_for_entity, history_factor, repeat_reviewer_factor, final_weight,
            credibility_breakdown
        FROM vw_credibility_weights
        WHERE entity_id = %s
        ORDER BY created_at DESC, rating_id DESC
        ''',
        (entity_id,)
    )

    feedback = fetch_all(
        '''
        SELECT id, user_name, rating_value, feedback_text, created_at
        FROM entity_feedback
        WHERE entity_id = %s
        ORDER BY created_at DESC, id DESC
        ''',
        (entity_id,)
    )

    return jsonify({
        'entity': entity,
        'ratings': ratings,
        'feedback': feedback
    })


@app.route('/api/entities/<int:entity_id>/feedback', methods=['POST'])
def submit_entity_feedback(entity_id):
    payload = request.get_json(silent=True) or {}
    user_name = (payload.get('user_name') or '').strip()
    rating_value = int(payload.get('rating_value') or 0)
    feedback_text = (payload.get('feedback_text') or '').strip()

    if not user_name or not feedback_text or rating_value < 1 or rating_value > 5:
        return jsonify({'error': 'User name, star rating, and feedback text are required.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute('SELECT id FROM entities WHERE id = %s', (entity_id,))
        entity = cursor.fetchone()

        if entity is None:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Entity not found'}), 404

        user_id = get_or_create_user(conn, user_name)

        cursor.execute(
            '''
            INSERT INTO ratings (user_id, entity_id, rating_value, review_text)
            VALUES (%s, %s, %s, %s)
            ''',
            (user_id, entity_id, rating_value, feedback_text)
        )
        rating_id = cursor.lastrowid

        refresh_user_reputation(conn, user_id)

        cursor.execute(
            '''
            INSERT INTO entity_feedback (entity_id, user_name, rating_value, feedback_text)
            VALUES (%s, %s, %s, %s)
            ''',
            (entity_id, user_name, rating_value, feedback_text)
        )
        feedback_id = cursor.lastrowid
        conn.commit()

        cursor.execute(
            '''
            SELECT id, user_name, rating_value, feedback_text, created_at
            FROM entity_feedback
            WHERE id = %s
            ''',
            (feedback_id,)
        )
        feedback = cursor.fetchone()
    except Error as exc:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'error': f'Database error: {exc}'}), 500

    cursor.close()
    conn.close()

    return jsonify({
        'message': 'Feedback submitted successfully.',
        'feedback': feedback,
        'rating_id': rating_id
    }), 201


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_details(user_id):
    user = fetch_one('SELECT id, username, join_date, is_verified, reputation_score FROM users WHERE id = %s', (user_id,))
    if user is None:
        return jsonify({'error': 'User not found'}), 404

    ratings = fetch_all(
        '''
        SELECT
            r.id as rating_id, r.rating_value, r.review_text, r.created_at,
            e.id as entity_id, e.name as entity_name,
            vw.final_weight, vw.credibility_breakdown
        FROM ratings r
        JOIN entities e ON r.entity_id = e.id
        LEFT JOIN vw_credibility_weights vw ON r.id = vw.rating_id
        WHERE r.user_id = %s
        ORDER BY r.created_at DESC
        ''',
        (user_id,)
    )

    return jsonify({
        'user': user,
        'ratings': ratings
    })


if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    print('Starting Flask server on http://127.0.0.1:5000')
    app.run(debug=True, port=5000)
