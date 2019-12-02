import requests
import logging
import time

from dash.orgs.tasks import org_task

logger = logging.getLogger(__name__)


@org_task("pull_channel_stats", 60 * 30)
def pull_channel_stats(org):
    from ureport.channels.models import ChannelStats, ChannelDailyStats, ChannelMonthlyStats

    start = time.time()
    backend = org.backends.first()

    channel_stats = request(backend, "channel_stats")
    for stats in channel_stats:
        channel = ChannelStats.update_or_create(
            org=org,
            uuid=stats.get("uuid"),
            channel_type=stats.get("channel_type"),
            msg_count=stats.get("msg_count"),
            ivr_count=stats.get("ivr_count"),
            error_count=stats.get("error_count"),
        )

        daily_count = stats.get("daily_count", [])
        if len(daily_count) > 0:
            for daily in daily_count:
                direction = daily.get("name")
                msg_type = daily.get("type")

                for data in daily.get("data"):
                    ChannelDailyStats.update_or_create(
                        channel=channel,
                        direction=direction,
                        type=msg_type,
                        date=data.get("date"),
                        count=data.get("count"),
                    )

        monthly_totals = stats.get("monthly_totals", [])
        if len(monthly_totals) > 0:
            for monthly in monthly_totals:
                ChannelMonthlyStats.update_or_create(
                    channel=channel,
                    date=monthly.get("month_start")[:10],
                    incoming_messages=monthly.get("incoming_messages_count"),
                    outgoing_messages=monthly.get("outgoing_messages_count"),
                    incoming_ivr=monthly.get("incoming_ivr_count"),
                    outgoing_ivr=monthly.get("outgoing_ivr_count"),
                    error_count=monthly.get("error_count"),
                )

    logger.info("Task: pull_channel_stats took %ss" % (time.time() - start))


def request(backend, endpoint):
    headers = {"Authorization": "Token {}".format(backend.api_token)}

    response = requests.get("{}/api/v2/{}.json".format(backend.host, endpoint), headers=headers)
    response = response.json()
    return response.get("results")
