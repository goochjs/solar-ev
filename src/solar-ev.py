"""
Created on 3 Nov 2022

@author: Jeremy Gooch

    Utilities to manage home solar and EV settings.

    Execute script with -h parameter for usage
"""

# --- LIBRARIES --------------------------------------------------------------

import argparse
import datetime
import logging
import os
from pathlib import Path
from typing import Dict

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

# --- CONSTANTS --------------------------------------------------------------

SCRIPT_PATH = Path(__file__).parent.absolute()
GIVENERGY_API_ENDPOINT = os.environ.get("GIVENERGY_API_ENDPOINT")
GIVENERGY_API_KEY = os.environ.get("GIVENERGY_API_KEY")
OCTOPUS_ACCOUNT_NUMBER = os.environ.get("OCTOPUS_ACCOUNT_NUMBER")
OCTOPUS_API_ENDPOINT = os.environ.get("OCTOPUS_API_ENDPOINT")
OCTOPUS_API_KEY = os.environ.get("OCTOPUS_API_KEY")
PLANNED_DISPATCHES_GQL = os.environ.get("PLANNED_DISPATCHES_GQL")
TOKEN_MUTATION_GQL = os.environ.get("TOKEN_MUTATION_GQL")

# --- FUNCTIONS --------------------------------------------------------------


def _process_options() -> None:
    opts = argparse.ArgumentParser(description="Solar and EV control")

    opts.add_argument(
        "--verbose",
        "-v",
        required=False,
        default=False,
        action="store_true",
        help="Send log messages to sysout",
    )
    options = opts.parse_args()

    if options.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(levelname)s] (%(threadName)-10s) %(message)s",
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] (%(threadName)-10s) %(message)s",
        )


def _load_gql(path: str):
    with open(path) as f:
        return gql(f.read())


def _token_variables(api_key: str) -> Dict:
    return {"input": {"APIKey": api_key}}


def _account_number_variables(account_number: str) -> Dict:
    return {"accountNumber": account_number}


def _call_graphql(api_endpoint: str, headers: Dict, gql_input, variables: Dict):
    api_transport = AIOHTTPTransport(url=api_endpoint, headers=headers)
    api_client = Client(transport=api_transport)
    return api_client.execute(gql_input, variable_values=variables)


def _is_car_plugged_in() -> bool:
    """
    Work out whether the car is plugged in.
    """
    # Get a token for Octopus' API
    logging.debug("Calling Octopus for an API token")
    token_dict = _call_graphql(
        api_endpoint=OCTOPUS_API_ENDPOINT,
        headers={},
        gql_input=_load_gql(f"{SCRIPT_PATH}/{TOKEN_MUTATION_GQL}"),
        variables=_token_variables(OCTOPUS_API_KEY),
    )
    octopus_token = token_dict["obtainKrakenToken"]["token"]

    # See if any dispatches are planned (i.e. the EV charging plan)
    # This will tell us if the car is plugged in
    logging.debug("Calling Octopus for EV dispatch data")
    dispatches_dict = _call_graphql(
        api_endpoint=OCTOPUS_API_ENDPOINT,
        headers={"Authorization": f"JWT {octopus_token}"},
        gql_input=_load_gql(f"{SCRIPT_PATH}/{PLANNED_DISPATCHES_GQL}"),
        variables=_account_number_variables(OCTOPUS_ACCOUNT_NUMBER),
    )

    if dispatches_dict["plannedDispatches"]:
        # TODO: find the latest dispatch to see
        # if it's after the battery start time
        log_message = f"Dispatches found {dispatches_dict}"
        logging.debug(log_message)
        return True
    else:
        # TODO: If no dispatches, then just make sure the home battery chsrge is on
        logging.debug("No dispatches found")
        return False


# --- START OF MAIN ----------------------------------------------------------


def main():
    """Let's do stuff."""
    _process_options()
    start_time = datetime.datetime.now()
    log_message = f"{start_time.strftime('%Y-%m-%d %I:%M:%S %p')} Started"
    logging.debug(log_message)

    if _is_car_plugged_in():
        logging.info("Car is plugged in")
    else:
        logging.info("Car is not plugged in")

    # Wrapping up
    end_time = datetime.datetime.now()
    exec_time = end_time - start_time
    log_message = f"Execution time {str(exec_time)}"
    logging.debug(log_message)
    log_message = f"{end_time.strftime('%Y-%m-%d %I:%M:%S %p')} Finished"
    logging.debug(log_message)


# --- END OF MAIN ------------------------------------------------------------


if __name__ == "__main__":
    main()
