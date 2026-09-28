import asyncio
import os
from datetime import datetime, timedelta

from kasa import Discover


# ============================================================
# CONFIGURATION
# ============================================================

IP = "172.23.254.95"

USERNAME = os.environ["KASA_USERNAME"]
PASSWORD = os.environ["KASA_PASSWORD"]

OUTPUT_FILE = "p110_solar_energy.txt"

# Electricity value / savings calculation
UNIT_COST = 7.00       # ₹ per kWh

# How far back should we look for historical monthly data?
# Increase this if your P110 has been installed for longer.
OLDEST_YEAR = 2015


# ============================================================
# HELPERS
# ============================================================

def timestamp(dt):
    """Convert local datetime to Unix timestamp."""
    return int(dt.timestamp())


def format_energy(wh):
    """Return nicely formatted Wh and kWh."""
    return (
        f"{wh:,.0f}",
        f"{wh / 1000:,.3f}",
    )


def format_rupees(amount):
    """Return nicely formatted Indian Rupee amount."""
    return f"₹{amount:,.2f}"


async def query_energy(dev, start, end, interval):
    """Query the raw Tapo get_energy_data API."""

    response = await dev.protocol.query({
        "get_energy_data": {
            "start_timestamp": timestamp(start),
            "end_timestamp": timestamp(end),
            "interval": interval,
        }
    })

    return response["get_energy_data"]


# ============================================================
# MONTHLY HISTORY
# ============================================================

async def get_monthly(dev, year):

    start = datetime(year, 1, 1)
    end = datetime(year + 1, 1, 1)

    result = await query_energy(
        dev,
        start,
        end,
        43200,
    )

    data = result.get("data", [])

    if not data:
        return []

    response_start = datetime.fromtimestamp(
        result["start_timestamp"]
    )

    rows = []

    for i, wh in enumerate(data):

        month_index = response_start.month - 1 + i

        row_year = (
            response_start.year
            + month_index // 12
        )

        row_month = (
            month_index % 12
        ) + 1

        rows.append({
            "year": row_year,
            "month": row_month,
            "month_name": datetime(
                row_year,
                row_month,
                1,
            ).strftime("%B"),
            "energy_wh": wh,
        })

    return rows


# ============================================================
# FIND ALL MONTHLY HISTORY
# ============================================================

async def get_all_monthly(dev):

    current_year = datetime.now().year

    all_rows = []

    print()
    print("Searching for historical monthly data...")
    print()

    for year in range(
        OLDEST_YEAR,
        current_year + 1,
    ):

        print(
            f"Checking monthly history: {year}",
            end=" ... ",
            flush=True,
        )

        try:

            rows = await get_monthly(
                dev,
                year,
            )

            total = sum(
                row["energy_wh"]
                for row in rows
            )

            if total > 0:

                print(
                    f"{total / 1000:,.3f} kWh"
                )

                all_rows.extend(rows)

            else:

                print("no energy data")

        except Exception as exc:

            print(
                f"error: {exc}"
            )

    return all_rows


# ============================================================
# DAILY HISTORY
# ============================================================

async def get_daily(
    dev,
    start_date,
    end_date,
):

    rows = []

    # Align to beginning of quarter
    quarter_month = (
        ((start_date.month - 1) // 3) * 3
    ) + 1

    date = datetime(
        start_date.year,
        quarter_month,
        1,
    )

    while date < end_date:

        if date.month == 10:

            quarter_end = datetime(
                date.year + 1,
                1,
                1,
            )

        else:

            quarter_end = datetime(
                date.year,
                date.month + 3,
                1,
            )

        print(
            f"Daily: "
            f"{date:%Y-%m-%d} -> "
            f"{quarter_end:%Y-%m-%d}"
        )

        result = await query_energy(
            dev,
            date,
            quarter_end,
            1440,
        )

        data = result.get("data", [])

        response_start = datetime.fromtimestamp(
            result["start_timestamp"]
        )

        for i, wh in enumerate(data):

            dt = (
                response_start
                + timedelta(days=i)
            )

            if start_date <= dt < end_date:

                rows.append({
                    "date": dt.strftime(
                        "%Y-%m-%d"
                    ),
                    "energy_wh": wh,
                })

        date = quarter_end

    return rows


# ============================================================
# HOURLY HISTORY
# ============================================================

async def get_hourly(
    dev,
    start_date,
    end_date,
):

    rows = []

    date = start_date

    while date < end_date:

        next_date = (
            date + timedelta(days=1)
        )

        print(
            f"Hourly: "
            f"{date:%Y-%m-%d}"
        )

        result = await query_energy(
            dev,
            date,
            next_date,
            60,
        )

        data = result.get("data", [])

        response_start = datetime.fromtimestamp(
            result["start_timestamp"]
        )

        for i, wh in enumerate(data):

            dt = (
                response_start
                + timedelta(hours=i)
            )

            rows.append({
                "timestamp": dt.strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "energy_wh": wh,
            })

        date = next_date

    return rows


# ============================================================
# REPORT FORMATTING
# ============================================================

def write_separator(
    f,
    char="-",
    width=88,
):
    f.write(char * width + "\n")


def write_section(
    f,
    title,
    width=88,
):

    f.write("\n")
    write_separator(
        f,
        "-",
        width,
    )

    f.write(title + "\n")

    write_separator(
        f,
        "-",
        width,
    )

    f.write("\n")


def write_title(
    f,
    title,
    width=88,
):

    f.write("=" * width + "\n")
    f.write(title.center(width) + "\n")
    f.write("=" * width + "\n")


# ============================================================
# WRITE REPORT
# ============================================================

def write_report(
    filename,
    device,
    ip,
    monthly,
    daily,
    hourly,
):

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as f:

        # ====================================================
        # CALCULATIONS
        # ====================================================

        total_wh = sum(
            row["energy_wh"]
            for row in monthly
        )

        total_kwh = total_wh / 1000

        total_savings = (
            total_kwh * UNIT_COST
        )

        # ====================================================
        # HEADER
        # ====================================================

        write_title(
            f,
            "TAPO P110 SOLAR ENERGY HISTORY",
        )

        f.write(
            f"Device       : {device}\n"
        )

        f.write(
            f"IP Address   : {ip}\n"
        )

        f.write(
            f"Generated    : "
            f"{datetime.now():%Y-%m-%d %H:%M:%S}\n"
        )

        f.write(
            f"Unit Value   : "
            f"{format_rupees(UNIT_COST)} / kWh\n"
        )

        f.write(
            "Measurement  : Solar energy generated\n"
        )

        # ====================================================
        # YEARLY
        # ====================================================

        write_section(
            f,
            "YEARLY SOLAR ENERGY GENERATION",
        )

        f.write(
            f"{'Year':<14}"
            f"{'Energy (Wh)':>18}"
            f"{'Energy (kWh)':>20}"
            f"{'Savings':>22}\n"
        )

        f.write(
            f"{'-' * 14}"
            f"{'-' * 18}"
            f"{'-' * 20}"
            f"{'-' * 22}\n"
        )

        yearly = {}

        for row in monthly:

            year = row["year"]

            yearly.setdefault(
                year,
                0,
            )

            yearly[year] += (
                row["energy_wh"]
            )

        for year in sorted(yearly):

            wh = yearly[year]
            kwh = wh / 1000
            savings = kwh * UNIT_COST

            f.write(
                f"{year:<14}"
                f"{wh:>18,.0f}"
                f"{kwh:>20,.3f}"
                f"{format_rupees(savings):>22}\n"
            )

        f.write("\n")

        f.write(
            f"{'TOTAL':<14}"
            f"{total_wh:>18,.0f}"
            f"{total_kwh:>20,.3f}"
            f"{format_rupees(total_savings):>22}\n"
        )

        # ====================================================
        # MONTHLY
        # ====================================================

        write_section(
            f,
            "MONTHLY SOLAR ENERGY GENERATION",
        )

        f.write(
            f"{'Year':<10}"
            f"{'Month':<14}"
            f"{'Energy (Wh)':>18}"
            f"{'Energy (kWh)':>20}"
            f"{'Savings':>22}\n"
        )

        f.write(
            f"{'-' * 10}"
            f"{'-' * 14}"
            f"{'-' * 18}"
            f"{'-' * 20}"
            f"{'-' * 22}\n"
        )

        current_year = None
        year_total = 0

        for row in monthly:

            year = row["year"]

            # Print subtotal when year changes
            if (
                current_year is not None
                and year != current_year
            ):

                f.write("\n")

                wh_text, kwh_text = (
                    format_energy(year_total)
                )

                f.write(
                    f"{current_year} TOTAL"
                    f"{'':<8}"
                    f"{wh_text:>18}"
                    f"{kwh_text:>20}"
                    f"{format_rupees(year_total / 1000 * UNIT_COST):>22}\n"
                )

                f.write("\n")

                year_total = 0

            current_year = year

            wh = row["energy_wh"]

            year_total += wh

            wh_text, kwh_text = (
                format_energy(wh)
            )

            savings = (
                wh / 1000
            ) * UNIT_COST

            f.write(
                f"{year:<10}"
                f"{row['month_name']:<14}"
                f"{wh_text:>18}"
                f"{kwh_text:>20}"
                f"{format_rupees(savings):>22}\n"
            )

        # Final yearly subtotal
        if current_year is not None:

            f.write("\n")

            wh_text, kwh_text = (
                format_energy(year_total)
            )

            f.write(
                f"{current_year} TOTAL"
                f"{'':<8}"
                f"{wh_text:>18}"
                f"{kwh_text:>20}"
                f"{format_rupees(year_total / 1000 * UNIT_COST):>22}\n"
            )

        # ====================================================
        # DAILY
        # ====================================================

        write_section(
            f,
            "DAILY SOLAR ENERGY GENERATION",
        )

        f.write(
            f"{'Date':<16}"
            f"{'Energy (Wh)':>18}"
            f"{'Energy (kWh)':>20}"
            f"{'Savings':>22}\n"
        )

        f.write(
            f"{'-' * 16}"
            f"{'-' * 18}"
            f"{'-' * 20}"
            f"{'-' * 22}\n"
        )

        daily_total = 0

        for row in daily:

            wh = row["energy_wh"]

            daily_total += wh

            wh_text, kwh_text = (
                format_energy(wh)
            )

            savings = (
                wh / 1000
            ) * UNIT_COST

            f.write(
                f"{row['date']:<16}"
                f"{wh_text:>18}"
                f"{kwh_text:>20}"
                f"{format_rupees(savings):>22}\n"
            )

        if daily:

            f.write("\n")

            wh_text, kwh_text = (
                format_energy(daily_total)
            )

            f.write(
                f"{'TOTAL':<16}"
                f"{wh_text:>18}"
                f"{kwh_text:>20}"
                f"{format_rupees(daily_total / 1000 * UNIT_COST):>22}\n"
            )

        # ====================================================
        # HOURLY
        # ====================================================

        write_section(
            f,
            "HOURLY SOLAR ENERGY GENERATION",
        )

        f.write(
            f"{'Date':<16}"
            f"{'Time':<10}"
            f"{'Energy (Wh)':>18}"
            f"{'Energy (kWh)':>20}"
            f"{'Savings':>22}\n"
        )

        f.write(
            f"{'-' * 16}"
            f"{'-' * 10}"
            f"{'-' * 18}"
            f"{'-' * 20}"
            f"{'-' * 22}\n"
        )

        hourly_total = 0

        for row in hourly:

            wh = row["energy_wh"]

            hourly_total += wh

            wh_text, kwh_text = (
                format_energy(wh)
            )

            dt = datetime.strptime(
                row["timestamp"],
                "%Y-%m-%d %H:%M",
            )

            savings = (
                wh / 1000
            ) * UNIT_COST

            f.write(
                f"{dt:%Y-%m-%d}    "
                f"{dt:%H:%M}"
                f"{wh_text:>18}"
                f"{kwh_text:>20}"
                f"{format_rupees(savings):>22}\n"
            )

        if hourly:

            f.write("\n")

            wh_text, kwh_text = (
                format_energy(hourly_total)
            )

            f.write(
                f"{'TOTAL':<26}"
                f"{wh_text:>18}"
                f"{kwh_text:>20}"
                f"{format_rupees(hourly_total / 1000 * UNIT_COST):>22}\n"
            )

        # ====================================================
        # SAVINGS SUMMARY
        # ====================================================

        f.write("\n")

        write_title(
            f,
            "SOLAR SAVINGS SUMMARY",
        )

        f.write("\n")

        f.write(
            f"{'Total Solar Energy Generated':<42}"
            f"{total_kwh:>20,.3f} kWh\n"
        )

        f.write(
            f"{'Electricity Value':<42}"
            f"{format_rupees(UNIT_COST):>20} / kWh\n"
        )

        f.write(
            f"{'Total Electricity Savings':<42}"
            f"{format_rupees(total_savings):>20}\n"
        )

        f.write("\n")

        write_separator(
            f,
            "=",
            88,
        )

        f.write(
            "TOTAL SAVINGS FROM SOLAR GENERATION".center(88)
            + "\n"
        )

        f.write(
            format_rupees(total_savings).center(88)
            + "\n"
        )

        write_separator(
            f,
            "=",
            88,
        )

        f.write("\n")

        f.write(
            "Calculation: "
            f"{total_kwh:,.3f} kWh × "
            f"{format_rupees(UNIT_COST)}/kWh = "
            f"{format_rupees(total_savings)}\n"
        )

        f.write("\n")

        f.write("=" * 88 + "\n")
        f.write(
            "End of report".center(88) + "\n"
        )
        f.write("=" * 88 + "\n")


# ============================================================
# MAIN
# ============================================================

async def main():

    print()
    print("=" * 60)
    print("Connecting to Tapo P110...")
    print("=" * 60)

    dev = await Discover.discover_single(
        IP,
        username=USERNAME,
        password=PASSWORD,
    )

    print(
        f"Connected: {dev.model}"
    )

    try:

        # ====================================================
        # ALL MONTHLY HISTORY
        # ====================================================

        monthly = await get_all_monthly(
            dev
        )

        if not monthly:

            print()
            print(
                "No monthly energy history found."
            )
            return

        # ====================================================
        # DAILY HISTORY
        # ====================================================

        today = datetime.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        # Last 100 days
        daily_start = (
            today
            - timedelta(days=100)
        )

        print()
        print("Downloading daily history...")

        daily = await get_daily(
            dev,
            daily_start,
            today + timedelta(days=1),
        )

        # ====================================================
        # HOURLY HISTORY
        # ====================================================

        # Last 8 days
        hourly_start = (
            today
            - timedelta(days=8)
        )

        print()
        print("Downloading hourly history...")

        hourly = await get_hourly(
            dev,
            hourly_start,
            today + timedelta(days=1),
        )

        # ====================================================
        # WRITE REPORT
        # ====================================================

        write_report(
            OUTPUT_FILE,
            dev.model,
            IP,
            monthly,
            daily,
            hourly,
        )

        # ====================================================
        # CONSOLE SUMMARY
        # ====================================================

        total_wh = sum(
            row["energy_wh"]
            for row in monthly
        )

        total_kwh = total_wh / 1000

        savings = (
            total_kwh * UNIT_COST
        )

        print()
        print("=" * 60)
        print("DONE")
        print("=" * 60)
        print()
        print(
            f"Total solar generation : "
            f"{total_kwh:,.3f} kWh"
        )

        print(
            f"Electricity value      : "
            f"{format_rupees(UNIT_COST)} / kWh"
        )

        print(
            f"Total savings          : "
            f"{format_rupees(savings)}"
        )

        print()
        print(
            f"Report written to: "
            f"{OUTPUT_FILE}"
        )
        print()

    finally:

        await dev.protocol.close()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())

