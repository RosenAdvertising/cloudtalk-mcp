from pathlib import Path

from mcp_test_kit.config import (
    ResilienceConfig,
    SeedConfig,
    SmokeConfig,
    SpecCheckConfig,
    ToolkitConfig,
    WriteConfig,
    WriteStep,
)

from cloudtalk_mcp.server import mcp

_TESTS_DIR = Path(__file__).parent

TOOLKIT = ToolkitConfig(
    mcp_server=mcp,
    seed=SeedConfig(seed_script=_TESTS_DIR / "seed_data.py"),
    spec_check=SpecCheckConfig(
        endpoints_path=_TESTS_DIR.parent / "endpoints.yaml",
        openapi_path=_TESTS_DIR.parent / "endpoints.yaml",  # no published OpenAPI spec
    ),
    source_path=_TESTS_DIR.parent / "cloudtalk_mcp",
    module_path="cloudtalk_mcp",
    server_path=_TESTS_DIR.parent / "cloudtalk_mcp" / "server.py",
    smoke=SmokeConfig(
        server=mcp,
        read_tools=[
            "list_agents",
            "list_calls",
            "list_contacts",
            "list_numbers",
            "get_call_statistics",
        ],
    ),
    write=WriteConfig(
        server=mcp,
        steps=[
            # 1. Create contact — ID flows into update and delete
            # CloudTalk wraps the created ID at responseData.data.id
            WriteStep(
                tool="create_contact",
                args={
                    "first_name": "[write-test]",
                    "last_name": "WriteHarness",
                    "phone": "+12025559999",
                    "email": "write-harness@example.com",
                },
                state_key="contact_id",
                extract=lambda body: (
                    body.get("responseData", {}).get("data", {}).get("id")
                    or body.get("data", {}).get("id")
                    or body.get("id")
                ),
            ),
            # 2. Update the contact
            WriteStep(
                tool="update_contact",
                args=lambda s: {
                    "contact_id": s["contact_id"],
                    "first_name": "[write-test]",
                    "last_name": "WriteHarness-Updated",
                },
                skip_if_missing="contact_id",
            ),
            # 3. Delete the contact — cleanup
            WriteStep(
                tool="delete_contact",
                args=lambda s: {"contact_id": s["contact_id"]},
                skip_if_missing="contact_id",
                cleanup=True,
            ),
        ],
    ),
    resilience=ResilienceConfig(tools_to_timeout_test=["list_agents"]),
    skip_tiers={
        "contract": "no published OpenAPI spec for CloudTalk API",
    },
)
