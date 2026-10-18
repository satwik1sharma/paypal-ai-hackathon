import requests
from paypal_agent_toolkit.shared.configuration import Configuration, Context, is_tool_allowed
from paypal_agent_toolkit.shared.tools import tools as TOOLKIT_TOOLS

from paypal_ai_hackathon.paypal_tools import DEFAULT_ACTIONS, paypal_error_detail, to_openai_tools


def test_default_actions_enable_order_tools():
    config = Configuration(actions=DEFAULT_ACTIONS, context=Context(sandbox=True))
    names = {t["method"] for t in TOOLKIT_TOOLS if is_tool_allowed(t, config)}
    assert {"create_order", "get_order_details", "pay_order"} <= names


def test_openai_tool_shape():
    defs = to_openai_tools(TOOLKIT_TOOLS)
    assert len(defs) == len(TOOLKIT_TOOLS)
    for d in defs:
        assert d["type"] == "function"
        fn = d["function"]
        assert set(fn) == {"name", "description", "parameters"}
        assert fn["parameters"]["type"] == "object"
        assert fn["description"]


def test_paypal_error_detail_surfaces_issue():
    resp = requests.Response()
    resp.status_code = 422
    resp._content = (
        b'{"name":"UNPROCESSABLE_ENTITY","message":"The requested action could not be performed.",'
        b'"details":[{"issue":"ORDER_NOT_APPROVED","description":"Payer has not yet approved the Order."}]}'
    )
    detail = paypal_error_detail(requests.HTTPError(response=resp))
    assert "422" in detail
    assert "ORDER_NOT_APPROVED" in detail
