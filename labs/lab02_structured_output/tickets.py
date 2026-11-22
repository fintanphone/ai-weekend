"""Shared test data for Lab 2 — used by both structured.py and structured_local.py
so the API and local numbers are directly comparable.

Two tiers:

  Tier 1 — clean.  One sender, one company, an explicit reference, and a
           severity the customer more or less states. Any competent model
           should score 100%. These exist so the lab opens with something
           that works.

  Tier 2 — ambiguous. Each ticket targets one specific extraction failure.
           The right answer is unambiguous to a careful human; it is the
           *model* that finds it hard. This is where the two scoring columns
           come apart.

Every tier-2 answer is defensible under the three extraction rules stated in
RULES below, which are given to the model in both the prompt and the schema
descriptions. If the rules weren't stated, these would be bad test cases
rather than hard ones.
"""

SEVERITIES = ["low", "medium", "high", "critical"]

RULES = """Extraction rules:
- customer_name is the person who WROTE this ticket — the signature or sender.
  Other people mentioned in the body are not the customer.
- company is the organisation that the writer belongs to, even if other
  companies are named.
- severity reflects the ACTUAL impact described, not the urgency the customer
  claims. Someone shouting is not automatically critical; someone apologising
  for the bother may still be reporting an outage.
    low      cosmetic or trivial, no work is blocked
    medium   one feature or one account affected, a workaround exists
    high     a whole site, route or workflow is blocked
    critical production is down for all users
- reference_id is a support ticket reference, which always looks like two
  letters, a hyphen, then four digits (for example AF-7741). Invoice numbers,
  error codes, order numbers and references quoted from older closed tickets
  are NOT the reference for this ticket. Use null if this ticket has none."""

SCHEMA = {
    "type": "object",
    "properties": {
        "customer_name": {
            "type": "string",
            "description": "Full name of the person who WROTE this ticket — the "
                           "signature or sender, not anyone merely mentioned.",
        },
        "company": {
            "type": "string",
            "description": "The organisation the writer belongs to, even if other "
                           "companies are named in the body.",
        },
        "issue_summary": {
            "type": "string",
            "description": "One sentence, factual, no speculation.",
        },
        "severity": {
            "type": "string",
            "enum": SEVERITIES,
            "description": "Based on actual impact, not the customer's tone. "
                           "low=cosmetic, medium=one feature or account, "
                           "high=a whole site or workflow blocked, "
                           "critical=production down for all users.",
        },
        "reference_id": {
            "type": ["string", "null"],
            "description": "This ticket's support reference, format XX-NNNN. Not an "
                           "invoice number, error code, or a reference quoted from an "
                           "older closed ticket. null if none.",
        },
    },
    "required": ["customer_name", "company", "issue_summary", "severity", "reference_id"],
}

REQUIRED = set(SCHEMA["required"])


# --------------------------------------------------------------------------
# Schema variants — the experiment that matters most in this lab
# --------------------------------------------------------------------------
#
# SCHEMA above is the "lax" variant, and `reference_id` is the only nullable
# field in it. Its description also ends with "null if none", which hands the
# model a documented way to decline.
#
# On a hard ticket it takes that way out. Measured on claude-haiku-5-5, the
# relayed ticket (t9) returned reference_id=null on all three trials, even
# though a valid reference is present — costing method B three marks that
# method A, writing free text with no such affordance, scored.
#
# The "strict" variant removes BOTH the null type and the escape clause, and
# nothing else. Run the two against each other:
#
#     python structured.py --tier 2 --misses                  # lax
#     python structured.py --tier 2 --misses --schema strict   # strict
#
# The lesson is sharper than "schemas win". A schema guarantees shape. Its
# ACCURACY is a property of how you wrote it — a nullable type is a permission
# slip, and a description that lists escape routes will have them used.

def schema(variant: str = "lax") -> dict:
    """Return the tool schema. variant is 'lax', 'strict' or 'honest'."""
    import copy

    s = copy.deepcopy(SCHEMA)
    if variant == "strict":
        # Removes the null type AND the escape clause. Measured: recovers most
        # of t9, but the model then returns the STRING "null" instead - it
        # routes around the constraint rather than complying.
        #
        # Note what this schema now asserts: that every ticket has a reference.
        # Five of the six tier-2 tickets do not. So on those it forces the model
        # to invent a value, and norm_ref() quietly forgives "null"/"n/a" as
        # absence. This variant is a DISHONEST model of the domain, and that is
        # the point of keeping it: tightening a type cannot fix a prompt problem.
        s["properties"]["reference_id"] = {
            "type": "string",
            "description": "This ticket's support reference, format XX-NNNN. "
                           "Not an invoice number, error code, or a reference "
                           "quoted from an older closed ticket.",
        }
    elif variant == "honest":
        # Keeps the null, because the field genuinely IS optional here. Changes
        # only the prose: a positive instruction first, the exclusions second,
        # and null framed as the exception rather than an offer.
        s["properties"]["reference_id"] = {
            "type": ["string", "null"],
            "description": "This ticket's own support reference, in the format "
                           "XX-NNNN. Extract it whenever one is present, "
                           "including when the ticket was raised on someone "
                           "else's behalf. Do not use an invoice number, an "
                           "error code, or a reference quoted from an older "
                           "closed ticket. Use null only when the ticket "
                           "contains no reference of its own.",
        }
    elif variant != "lax":
        raise ValueError(
            f"unknown schema variant {variant!r}: use lax, strict or honest")
    return s


SCHEMA_VARIANTS = ("lax", "strict", "honest")

PROMPT_A = """Extract the details from this support ticket as JSON.

{rules}

Return ONLY a JSON object with keys: customer_name, company, issue_summary,
severity (one of: low, medium, high, critical), reference_id (or null).
No markdown, no code fences, no explanation.

Ticket:
{ticket}"""


TICKETS = [
    # ---------------------------------------------------------------- tier 1
    {
        "id": "t1-clean",
        "tier": 1,
        "traps": "none",
        "text": """Hi, this is Dervla Nolan from Aurora Freight. Our API integration
        started returning 502s at about 14:30 yesterday. It's blocking our overnight
        customs filing so it's pretty urgent. Ref AF-7741.""",
        "expect": {"surname": "nolan", "company": "aurora freight",
                   "reference_id": "af-7741", "severity": ["high", "critical"]},
    },
    {
        "id": "t2-trivial",
        "tier": 1,
        "traps": "none",
        "text": """morning - dashboard colours look a bit off on the new release? not a
        big deal, just flagging. tom @ Kestrel Analytics""",
        "expect": {"surname": "tom", "company": "kestrel analytics",
                   "reference_id": None, "severity": ["low"]},
    },
    {
        "id": "t3-outage",
        "tier": 1,
        "traps": "none",
        "text": """URGENT URGENT our entire production database is unreachable, every
        customer is down, we are losing money by the minute. Priya Raghavan,
        Meridian Health. This is ticket MH-0031 I think.""",
        "expect": {"surname": "raghavan", "company": "meridian health",
                   "reference_id": "mh-0031", "severity": ["critical"]},
    },

    # ---------------------------------------------------------------- tier 2
    {
        "id": "t4-two-companies",
        "tier": 2,
        "traps": "three companies named; the writer's is not the most prominent",
        "text": """Marek Lindqvist here, Baltic Haulage. We resell the Aurora Freight
        API on to our own customers, and one of them — Northwind Cold Chain — is
        reporting that label generation fails for any consignment over 30 items.
        Only affecting that one account as far as we can tell, and they can split
        the consignment as a workaround. No ticket ref that I know of.""",
        "expect": {"surname": "lindqvist", "company": "baltic haulage",
                   "reference_id": None, "severity": ["medium"]},
    },
    {
        "id": "t5-mentioned-person",
        "tier": 2,
        "traps": "a colleague is named before the signature",
        "text": """Following up on what Priya flagged last week — the export timeouts
        are back, same as before. Logs attached. Priya is on leave until the 14th so
        please reply to me directly rather than to her.

        Best,
        Aoife Brennan
        Systems Lead, Meridian Health""",
        "expect": {"surname": "brennan", "company": "meridian health",
                   "reference_id": None, "severity": ["medium", "high"]},
    },
    {
        "id": "t6-tone-vs-impact",
        "tier": 2,
        "traps": "customer downplays a site-wide outage",
        "text": """NOT URGENT, please don't page anyone out of hours. Just logging
        this for the record: since the release last night nobody in the Cork warehouse
        can scan inbound pallets, so the whole team is back to paper. We'll cope until
        Monday. Cheers, Declan Moore, Cork Logistics.""",
        "expect": {"surname": "moore", "company": "cork logistics",
                   "reference_id": None, "severity": ["high", "critical"]},
    },
    {
        "id": "t7-false-reference",
        "tier": 2,
        "traps": "an invoice number and an error code that look like references",
        "text": """Invoice INV-88213 appears to have been generated twice for the same
        consignment. Our finance team spotted it this morning. When we try to void one
        of them the portal returns error code E-4402. Everything else is working
        normally. Sinead Kavanagh, Kestrel Analytics.""",
        "expect": {"surname": "kavanagh", "company": "kestrel analytics",
                   "reference_id": None, "severity": ["low", "medium"]},
    },
    {
        "id": "t8-quoted-thread",
        "tier": 2,
        "traps": "a closed ticket's reference is quoted below the new issue",
        "text": """Different problem this time — the customs document generator has
        been producing blank PDFs for all EU routes since yesterday afternoon. Nothing
        gets through.

        > On Tuesday you wrote:
        > Ticket AF-7741 has now been resolved and closed. Thanks for confirming.
        > — Aurora Freight Support

        Tomas Kowalczyk
        Vantage Shipping""",
        "expect": {"surname": "kowalczyk", "company": "vantage shipping",
                   "reference_id": None, "severity": ["high", "critical"]},
    },
    {
        "id": "t9-relayed",
        "tier": 2,
        "traps": "written on behalf of a third party; a valid reference is present",
        "text": """Raising this on behalf of a client. I'm the account manager at
        Harbour Point Consulting. The affected party is Greenway Produce — their
        overnight stock sync has been failing silently since the 3rd, and they only
        noticed when their counts drifted. It's still running for everyone else.
        Our reference is HP-2210. Please contact me rather than them.

        Regards,
        Ciara Whelan""",
        "expect": {"surname": "whelan", "company": "harbour point consulting",
                   "reference_id": "hp-2210", "severity": ["medium", "high"]},
    },

    # ----------------------------------------------------------------------
    # Company-attribution traps. All four test the same field by different
    # mechanisms, so you can see WHICH kind of confusion a model is prone to
    # rather than just that it got one wrong. Severity is deliberately
    # unambiguous in each, so a severity disagreement cannot be mistaken for
    # a company error.
    # ----------------------------------------------------------------------
    {
        "id": "t10-brand-as-verb",
        "tier": 2,
        "traps": "a famous brand used as a VERB, plus a second as a component maker",
        "text": """The mains pump on line 2 has stopped and will not restart.
        Tried to Google the problem but got nowhere, and the Siemens controller
        is only showing a generic fault code. Bottling is stopped until this is
        sorted.

        Tomás Nolan
        Eiris Water Treatment""",
        "expect": {"surname": "nolan", "company": "eiris water treatment",
                   "reference_id": None, "severity": ["high", "critical"]},
    },
    {
        "id": "t11-product-brand",
        "tier": 2,
        "traps": "two famous brands as products; the writer's company is only in the signature",
        "text": """I am having problems with my Dell monitor since the Windows
        update went through. It drops to a black screen every few minutes. I can
        still work off the laptop screen so it is not urgent, but it is slowing
        me down.

        Sinéad Barry
        Clonmel Veterinary Group""",
        "expect": {"surname": "barry", "company": "clonmel veterinary group",
                   "reference_id": None, "severity": ["low", "medium"]},
    },
    {
        "id": "t12-employer-is-brand",
        "tier": 2,
        "traps": "INVERTED: the writer's employer IS the famous brand, and the vendor is named more often",
        "text": """Raising this from the service desk side. Our Acme CRM licences
        stopped validating at 08:40 and none of the sixty agents on shift can log
        a ticket. Acme's status page says everything is green, which it plainly
        is not. I manage the desk here at Dell's Limerick site. Our reference is
        DL-4417.

        Jane Okafor""",
        "expect": {"surname": "okafor", "company": "dell",
                   "reference_id": "dl-4417", "severity": ["high", "critical"]},
    },
    {
        "id": "t13-common-noun",
        "tier": 2,
        "traps": "the company name also appears as a lowercase everyday word in the body",
        "text": """The orange warning light on the compressor has been on since
        Friday and the unit is running hot. We have throttled output as a
        precaution. Not down yet, but I would rather not wait for it to fail.

        Dervla Hughes
        Orange Facilities Management""",
        "expect": {"surname": "hughes", "company": "orange facilities management",
                   "reference_id": None, "severity": ["medium", "high"]},
    },
]


# --------------------------------------------------------------------------
# Scoring: shape and truth, deliberately kept apart
# --------------------------------------------------------------------------

def is_valid(obj) -> bool:
    """Would this survive contact with a downstream system?"""
    if not isinstance(obj, dict):
        return False
    if not REQUIRED.issubset(obj.keys()):
        return False
    return obj.get("severity") in SEVERITIES


def norm_ref(v):
    if v is None:
        return None
    s = str(v).strip().lower()
    return None if s in ("", "none", "null", "n/a", "na", "unknown", "-") else s


def accuracy(obj, expect):
    """Returns (correct, checked, list of what went wrong)."""
    if not isinstance(obj, dict):
        return 0, 4, ["unparseable"]

    wrong, score = [], 0

    if expect["surname"] in str(obj.get("customer_name", "")).lower():
        score += 1
    else:
        wrong.append(f"name={obj.get('customer_name')!r}")

    company = str(obj.get("company", "")).lower()
    if expect["company"] in company or (company and company in expect["company"]):
        score += 1
    else:
        wrong.append(f"company={obj.get('company')!r}")

    if norm_ref(obj.get("reference_id")) == expect["reference_id"]:
        score += 1
    else:
        wrong.append(f"ref={obj.get('reference_id')!r}")

    if obj.get("severity") in expect["severity"]:
        score += 1
    else:
        wrong.append(f"severity={obj.get('severity')!r}")

    return score, 4, wrong


def select(tier: str = "all") -> list:
    if tier == "all":
        return TICKETS
    return [t for t in TICKETS if t["tier"] == int(tier)]
