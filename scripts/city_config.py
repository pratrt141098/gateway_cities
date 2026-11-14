"""Canonical city geography and classification."""

CITY_FIPS = {
    "Attleboro": "1600000US2502690",
    "Barnstable": "1600000US2503690",
    "Brockton": "1600000US2509000",
    "Chelsea": "1600000US2513205",
    "Chicopee": "1600000US2513660",
    "Everett": "1600000US2521990",
    "Fall River": "1600000US2523000",
    "Fitchburg": "1600000US2523875",
    "Framingham": "1600000US2524960",
    "Haverhill": "1600000US2529405",
    "Holyoke": "1600000US2530840",
    "Lawrence": "1600000US2534550",
    "Leominster": "1600000US2535075",
    "Lowell": "1600000US2537000",
    "Lynn": "1600000US2537490",
    "Malden": "1600000US2537875",
    "Methuen": "1600000US2540675",
    "New Bedford": "1600000US2545000",
    "Peabody": "1600000US2552490",
    "Pittsfield": "1600000US2553960",
    "Quincy": "1600000US2555745",
    "Revere": "1600000US2556585",
    "Salem": "1600000US2559105",
    "Springfield": "1600000US2567000",
    "Taunton": "1600000US2569170",
    "Westfield": "1600000US2576030",
    "Worcester": "1600000US2582000",
    "Somerville": "1600000US2562535",
    "Weymouth": "1600000US2578972",
    "Marlborough": "1600000US2538715",
    "Boston": "1600000US2507000",
    "Cambridge": "1600000US2511000",
}

BENCHMARK_CITIES = {"Boston", "Cambridge"}

COMPARISON_CITIES = {
    "Somerville", "Weymouth", "Marlborough", "Framingham"
}

GATEWAY_CITIES = (
    set(CITY_FIPS)
    - BENCHMARK_CITIES
    - COMPARISON_CITIES
)

CITY_TYPE = {
    city: (
        "benchmark" if city in BENCHMARK_CITIES
        else "comparison" if city in COMPARISON_CITIES
        else "gateway"
    )
    for city in CITY_FIPS
}

FIPS_TO_CITY = {fips: city for city, fips in CITY_FIPS.items()}

assert len(GATEWAY_CITIES) == 26
assert len(CITY_FIPS) == 32
