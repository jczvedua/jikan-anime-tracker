import requests, random
from django.shortcuts import render, redirect
from django.db.models import F
from django.db.models.functions import Coalesce
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import AnimeListForm
from .models import AnimeList

def home(request):
    return redirect('anime_search')

def fetch_anilist(query, variables):
    url = "https://graphql.anilist.co"

    try:
        response = requests.post(url, json={
            "query": query,
            "variables": variables
        }, timeout=5)

        if response.status_code == 200:
            return response.json()
    except requests.RequestException as e:
        print("Anilist error: ", e)
    return None

def quick_watching_list(request):
    ids = []
    db_list = AnimeList.objects.filter(status="watching", is_active=True)
    for anime in db_list:
        ids.append(anime.anilist_id)

    query = """
    query ($ids: [Int]){
        Page{
            media(id_in: $ids, type: ANIME){
                id
                coverImage{
                    large
                }
                episodes
            }
        }
    }
    """
    variables = {
        "ids": ids
    }

    list_data = fetch_anilist(query, variables)
    if list_data:
        watching_list = list_data["data"]["Page"]["media"]

    image_map = {
        anime["id"]: anime.get("coverImage",{}).get("large")
        for anime in watching_list
    }
    for anime in db_list:
        anime.image_url = image_map.get(anime.anilist_id)
    
    return db_list

def anime_search(request):
    query_text = request.GET.get('q', '').lower()
    anime_list = []

    if query_text:
        query = """
        query ($search: String) {
            Page(perPage: 10){
                media(search: $search, type: ANIME){
                    id
                    title {
                        romaji
                    }
                    coverImage {
                        large
                    }
                }
            }
        }
        """
        variables = {
            "search": query_text
        }

        data = fetch_anilist(query, variables)

        if data:
            anime_list = data["data"]["Page"]["media"]
        else:
            anime_list = []

    watching_list = quick_watching_list(request)

    return render(request, 'anime/search.html', {
        'anime_list': anime_list, 
        'query': query_text, 
        "watching": watching_list
        }
    )

def anime_view(request, anime_id):
    query = """
    query ($id: Int){
        Media(id: $id, type: ANIME){
        id
        title{
            romaji
        }
        coverImage{
            large
            }
        status
        episodes
        description
        }
    }
    """
    variables = {
        "id": anime_id
    }

    data = fetch_anilist(query, variables)
    if data:
        anime = data["data"]["Media"]

        list_entry = AnimeList.objects.filter(anilist_id=anime["id"], is_active=True).first()
        form = AnimeListForm(instance=list_entry) if list_entry else AnimeListForm()
        return render(request, "anime/view.html", {"anime": anime, "form": form, "list_entry": list_entry })

def random_anime(request):
    query = """
    query ($page: Int){
        Page(page: $page, perPage:10){
            media(type: ANIME){
                id
            }
        }
    }
    """
    variables = {"page": random.randint(1, 100)}

    data = fetch_anilist(query, variables)
    if data:
        media_list = data["data"]["Page"]["media"]

        if media_list:
            anime = random.choice(media_list)
            return redirect('anime_view', anime_id=anime["id"])

def add_to_list(request, anime_id):
    if request.method == "POST":
        query = """
        query ($id: Int){
            Media(id: $id, type: ANIME){
                id
                episodes
            }
        }
        """
        variables = {
            "id": anime_id
        }

        data = fetch_anilist(query, variables)
        if data:
            anime = data["data"]["Media"]
            form = AnimeListForm(request.POST)

            if form.is_valid():
                progress = form.cleaned_data.get("progress")
                total_episodes = anime.get("episodes")

                if progress is not None and total_episodes is not None:
                    if progress > total_episodes:
                        form.add_error("progress", "Invalid number")
                        return redirect("anime_view", anime_id=anime_id)

                obj, created = AnimeList.objects.update_or_create(
                    anilist_id=anime["id"],
                    defaults={
                        "status": form.cleaned_data["status"],
                        "progress": form.cleaned_data["progress"],
                        "score": form.cleaned_data["score"],
                        "is_active": True,
                        "total_episodes": anime["episodes"]    
                    })

                if obj.progress is not None and anime.get("episodes") is not None and obj.progress == anime["episodes"]:
                    obj.status = "completed"
                obj.save()

    return redirect("anime_view", anime_id=anime_id)

def view_list(request):
    watching_list = AnimeList.objects.filter(status="watching", is_active=True)
    planning_list = AnimeList.objects.filter(status="planning", is_active=True)
    completed_list = AnimeList.objects.filter(status="completed", is_active=True)
    paused_list = AnimeList.objects.filter(status="paused", is_active=True)
    dropped_list = AnimeList.objects.filter(status="dropped", is_active=True)

    context = {
        "watching": watching_list,
        "planning": planning_list,
        "completed": completed_list,
        "paused": paused_list,
        "dropped": dropped_list
    }

    ids = []
    for list_name, anime_list in context.items():
        ids.extend(anime.anilist_id for anime in anime_list)

    query = """
    query ($ids: [Int]){
        Page{
            media(id_in: $ids, type: ANIME){
                id
                title{
                    english
                    romaji
                    native
                }
                coverImage{
                    large
                }
                episodes
            }
        }
    }
    """
    variables = {
        "ids": ids
    }

    data = fetch_anilist(query, variables)
    anime_map = {}

    if data: 
        anime_map = { 
            item["id"]: item 
            for item in data["data"]["Page"]["media"]
        }
    for list_name, anime_list in context.items():
        for anime in anime_list:
            api = anime_map.get(anime.anilist_id, {})

            anime.title = api.get("title", {}).get("english") or api.get("title", {}).get("romaji") or api.get("title", {}).get("native")
            anime.image_url = api.get("coverImage", {}).get("large")
            ## anime.total_episodes = api.get("episodes")

    return render(request, 'anime/list.html', context)

def deactivate_anime(request, anime_id):
    if request.method == "POST":
        AnimeList.objects.filter(anilist_id=anime_id).update(
            status = "planning",
            progress = None,
            score = None,
            is_active = False
        )

    return redirect("view_list")

def quick_progress_increment(request, anime_id):
    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        AnimeList.objects.filter(anilist_id=anime_id).update(
            progress = Coalesce(F("progress"), 0) + 1
        )
    
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
        return redirect(next_url)
    return redirect("view_list")
