import asyncio
import importlib
import os
import sys
import traceback

import aiohttp
from aiohttp import web

from gidgethub import aiohttp as gh_aiohttp
from gidgethub import routing
from gidgethub import sansio
import joblib
model = joblib.load('./notebooks/model1.sav')
routes = web.RouteTableDef()
router = routing.Router()
def pred_label( author, title , description):
    X = [title] + [description]
    label = model.predict(X)
    return label[0]


@router.register("issues", action="opened")
async def issue_opened_event(event, gh,*arg, **kwargs) :

    issues = event.data["issue"] ["author"] ["title"] ["description"]
    label = pred_label(issues["author"],  issues["title"], issues["description"])
    await gh.post(issues["labels_url"], data=[label])

@routes.post("/")
async def main(request):
    body = await request.read()

    secret = os.environ.get("GH_SECRET")
    oauth_token = os.environ.get("GH_AUTH")

    event = sansio.Event.from_http(request.headers, body, secret=secret)
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "Srinikstudent",
                                  oauth_token=oauth_token)
        await router.dispatch(event, gh)
    return web.Response(status=200)


if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port=port)
