#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CineMatch Backend - 100% Legal e AdSense Ready
Backgrounds dinâmicos sem usar imagens de terceiros
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import random
import os

app = Flask(__name__)
CORS(app)

# Configuração
DEBUG = os.getenv('DEBUG', 'False') == 'True'
PORT = int(os.getenv('PORT', 5000))

# Carregar base de dados local
def load_movies():
    """Carregar filmes do JSON local"""
    try:
        with open('movies_database.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data['movies']
    except Exception as e:
        print(f"[ERROR] Failed to load movies: {e}")
        return []

MOVIES = load_movies()

# ============================================
# HELPER FUNCTIONS
# ============================================

def filter_movies(filters):
    """Filtrar filmes baseado nos critérios"""
    filtered = MOVIES.copy()
    
    # Filtro de rating
    if filters.get('min_rating'):
        min_rating = float(filters['min_rating'])
        filtered = [m for m in filtered if m.get('rating', 0) >= min_rating]
    
    # Filtro de ano
    if filters.get('year_min'):
        year_min = int(filters['year_min'])
        filtered = [m for m in filtered if m.get('year', 0) >= year_min]
    
    if filters.get('year_max'):
        year_max = int(filters['year_max'])
        filtered = [m for m in filtered if m.get('year', 9999) <= year_max]
    
    # Filtro de gênero
    if filters.get('genre'):
        genre = filters['genre']
        filtered = [m for m in filtered if genre in m.get('genres', [])]
    
    # Filtro de duração
    if filters.get('max_runtime'):
        max_runtime = int(filters['max_runtime'])
        if max_runtime < 999:  # 999 significa "any length"
            filtered = [m for m in filtered if m.get('runtime', 0) <= max_runtime]
    
    return filtered

def get_all_genres():
    """Extrair todos os gêneros únicos"""
    genres = set()
    for movie in MOVIES:
        genres.update(movie.get('genres', []))
    return sorted(list(genres))

def generate_reason(movie, filters):
    """Gerar razão da sugestão baseada nos filtros e características do filme"""
    reasons = []
    
    # Razão por gênero solicitado
    if filters.get('genre'):
        genre = filters['genre']
        genre_reasons = {
            'Drama': 'Compelling dramatic storytelling that explores the human condition',
            'Action': 'Intense action sequences with breathtaking choreography',
            'Comedy': 'Entertaining comedic moments that will make you laugh',
            'Sci-Fi': 'Mind-bending science fiction concepts that challenge reality',
            'Crime': 'Gripping crime narrative with intricate plot twists',
            'Thriller': 'Suspenseful thriller elements that keep you on edge',
            'Horror': 'Terrifying horror experience with atmospheric tension',
            'Romance': 'Heartwarming romantic journey that touches the soul',
            'Adventure': 'Epic adventure experience across incredible landscapes',
            'Fantasy': 'Magical fantasy world with imaginative storytelling',
            'Animation': 'Beautifully animated masterpiece with universal appeal',
            'War': 'Powerful war narrative examining courage and sacrifice',
            'History': 'Compelling historical drama bringing the past to life',
            'Mystery': 'Intriguing mystery puzzle that unfolds brilliantly',
            'Music': 'Outstanding musical experience celebrating artistry',
            'Biography': 'Inspiring biographical story of remarkable individuals',
            'Western': 'Classic western tale of justice and frontier life',
            'Film-Noir': 'Atmospheric noir with shadowy cinematography',
            'Family': 'Heartwarming family film for all ages'
        }
        reasons.append(genre_reasons.get(genre, f'Outstanding {genre.lower()} film'))
    
    # Razão por rating
    rating = movie.get('rating', 0)
    if rating >= 9.0:
        reasons.append('Universally acclaimed masterpiece')
    elif rating >= 8.7:
        reasons.append('Among the greatest films ever made')
    elif rating >= 8.5:
        reasons.append('Critically praised excellence')
    elif rating >= 8.3:
        reasons.append('Outstanding cinematic achievement')
    elif rating >= 8.0:
        reasons.append('Highly recommended by audiences worldwide')
    
    # Razão por época
    year = movie.get('year', 0)
    if year:
        current_year = 2025
        age = current_year - year
        if age <= 2:
            reasons.append('Fresh release with modern sensibilities')
        elif age <= 5:
            reasons.append('Recent gem with contemporary relevance')
        elif age <= 10:
            reasons.append('Modern classic already standing the test of time')
        elif 15 <= age <= 25:
            reasons.append('Influential film that shaped cinema')
        elif 25 <= age <= 40:
            reasons.append('Timeless masterpiece from cinema\'s golden age')
        elif age > 40:
            reasons.append('Historic cinematic treasure')
    
    # Razão por duração se foi filtrado
    if filters.get('max_runtime'):
        runtime = movie.get('runtime', 0)
        max_runtime = int(filters['max_runtime'])
        if runtime <= 90:
            reasons.append('Perfectly paced without a wasted moment')
        elif runtime <= 120:
            reasons.append('Ideal runtime for maximum engagement')
        elif runtime <= 150:
            reasons.append('Epic scope with rewarding depth')
    
    # Razões especiais por combinações de gêneros
    genres = movie.get('genres', [])
    if 'Crime' in genres and 'Drama' in genres:
        reasons.append('Masterful blend of crime and character study')
    elif 'Action' in genres and 'Sci-Fi' in genres:
        reasons.append('Thrilling fusion of action and futuristic concepts')
    elif 'Romance' in genres and 'Drama' in genres:
        reasons.append('Emotionally powerful love story')
    
    # Garantir pelo menos duas razões
    if len(reasons) < 2:
        reasons.append('Carefully selected for exceptional quality')
    
    return ' • '.join(reasons[:3])  # Máximo 3 razões

# ============================================
# ROUTES
# ============================================

@app.route('/')
def home():
    """Servir frontend"""
    return send_from_directory('.', 'index.html')

@app.route('/api/suggest', methods=['POST'])
def suggest_movie():
    """Endpoint principal - sugerir filme"""
    try:
        data = request.get_json() or {}
        
        # Filtros opcionais
        filters = {
            'min_rating': data.get('minRating'),
            'year_min': data.get('yearMin'),
            'year_max': data.get('yearMax'),
            'genre': data.get('genre'),
            'max_runtime': data.get('maxRuntime')
        }
        
        # Remover None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        print(f"[SUGGEST] Filters: {filters}")
        
        # Filtrar filmes
        filtered_movies = filter_movies(filters)
        
        if not filtered_movies:
            return jsonify({
                'success': False,
                'error': 'No movies found with these filters. Try adjusting your preferences.'
            }), 404
        
        # Escolher filme aleatório
        movie = random.choice(filtered_movies)
        
        # Gerar razão
        reason = generate_reason(movie, filters)
        
        # Montar resposta
        result = {
            'success': True,
            'movie': {
                'id': movie['id'],
                'title': movie['title'],
                'tagline': movie.get('tagline', ''),
                'overview': movie.get('overview', ''),
                'year': movie.get('year'),
                'rating': movie.get('rating', 0),
                'runtime': movie.get('runtime'),
                'genres': movie.get('genres', []),
                'director': movie.get('director', ''),
                'cast': ', '.join(movie.get('cast', [])),
                'trailer': None,
                'streaming': [],
                'imdb_id': movie.get('imdb_id'),
                'reason': reason
            }
        }
        
        print(f"[SUCCESS] Suggested: {movie['title']} ({movie.get('year')}) - Rating: {movie.get('rating')}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }), 500

@app.route('/api/genres', methods=['GET'])
def get_genres():
    """Obter lista de gêneros"""
    try:
        genres = get_all_genres()
        
        # Converter para formato esperado pelo frontend
        genre_list = [{'id': g, 'name': g} for g in genres]
        
        return jsonify({
            'success': True,
            'genres': genre_list
        })
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'CineMatch API',
        'version': '2.0',
        'movies_loaded': len(MOVIES),
        'genres_available': len(get_all_genres()),
        'legal_status': '100% AdSense Compatible'
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Estatísticas da base de dados"""
    try:
        ratings = [m.get('rating', 0) for m in MOVIES]
        years = [m.get('year', 0) for m in MOVIES if m.get('year')]
        
        return jsonify({
            'success': True,
            'stats': {
                'total_movies': len(MOVIES),
                'average_rating': round(sum(ratings) / len(ratings), 2) if ratings else 0,
                'highest_rated': max(ratings) if ratings else 0,
                'oldest_year': min(years) if years else 0,
                'newest_year': max(years) if years else 0,
                'genres': get_all_genres()
            }
        })
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    print("=" * 70)
    print("   🎬 CineMatch Backend v2.0 - Premium Edition")
    print("=" * 70)
    print(f"[DATABASE] {len(MOVIES)} movies loaded")
    print(f"[GENRES] {len(get_all_genres())} genres available")
    print(f"[LEGAL] 100% AdSense compatible - No third-party images")
    print(f"\n[ENDPOINTS]")
    print(f"  • Frontend: http://localhost:{PORT}")
    print(f"  • Suggest:  http://localhost:{PORT}/api/suggest")
    print(f"  • Genres:   http://localhost:{PORT}/api/genres")
    print(f"  • Health:   http://localhost:{PORT}/api/health")
    print(f"  • Stats:    http://localhost:{PORT}/api/stats")
    print("=" * 70)
    print(f"\n🚀 Server starting on port {PORT}...\n")
    
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)