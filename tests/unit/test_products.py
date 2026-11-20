"""Every product-page brief is complete: page text, the one shot, a hidden reference and its key."""
import json
import tomllib

import pytest

from suite import ROOT

PRODUCTS = sorted(d for d in (ROOT / "products").iterdir() if d.is_dir() and not d.name.startswith("_"))


@pytest.mark.parametrize("folder", PRODUCTS, ids=[d.name for d in PRODUCTS])
def test_product_is_complete(folder):
    meta = tomllib.loads((folder / "product.toml").read_text(encoding="utf-8"))
    assert meta["id"] == folder.name
    assert meta["page"] and meta["net_contents"] in meta["page"]
    assert (folder / "shot.png").is_file() and (folder / "reference.py").is_file()
    facts = json.loads((folder / "facts.json").read_text(encoding="utf-8"))
    assert set(facts["objects"]) == set(meta["objects"])
    assert all(o["open_edges"] == 0 and o["volume_ml"] > 0 for o in facts["objects"].values())


@pytest.mark.parametrize("folder", PRODUCTS, ids=[d.name for d in PRODUCTS])
def test_page_gives_no_dimensions(folder):
    """The point of a product-page brief: the only number is the net contents."""
    page = tomllib.loads((folder / "product.toml").read_text(encoding="utf-8"))["page"]
    assert " mm" not in page and "cm" not in page and "inch" not in page
