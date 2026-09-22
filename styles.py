import streamlit as st


def load_css():

    st.markdown(
        """
        <style>

        /* =========================
           GLOBAL
        ========================= */

        .stApp {
            background-color: #0D0D0D;
            color: white;
        }

        .main {
            background-color: #0D0D0D;
        }

        /* =========================
           SIDEBAR
        ========================= */

        section[data-testid="stSidebar"] {
            background-color: #111111;
            border-right: 1px solid #292929;
        }

        section[data-testid="stSidebar"] * {
            color: white;
        }

        /* =========================
           HEADER
        ========================= */

        .dashboard-header {

            padding: 25px 30px;

            border-radius: 15px;

            margin-bottom: 25px;

            background:
                linear-gradient(
                    135deg,
                    #171717,
                    #24090D
                );

            border: 1px solid #3A1519;
        }

        .dashboard-title {

            font-size: 32px;

            font-weight: 700;

            margin-bottom: 5px;
        }

        .dashboard-subtitle {

            color: #BBBBBB;

            font-size: 15px;
        }

        /* =========================
           KPI
        ========================= */

        .kpi-card {

            background-color: #161616;

            border: 1px solid #292929;

            border-radius: 12px;

            padding: 20px;

            min-height: 120px;
        }

        .kpi-title {

            color: #AAAAAA;

            font-size: 13px;

            margin-bottom: 10px;
        }

        .kpi-value {

            color: white;

            font-size: 27px;

            font-weight: 700;
        }

        .kpi-subtitle {

            color: #888888;

            font-size: 12px;

            margin-top: 6px;
        }

        /* =========================
           SECTION
        ========================= */

        .section-title {

            font-size: 22px;

            font-weight: 650;

            margin-top: 30px;

            margin-bottom: 15px;

            border-left: 4px solid #C1121F;

            padding-left: 12px;
        }

        /* =========================
           INSIGHT
        ========================= */

        .insight-card {

            background-color: #151515;

            border-left: 4px solid #C1121F;

            border-radius: 8px;

            padding: 15px;

            margin: 10px 0;
        }

        /* =========================
           FOOTER
        ========================= */

        .footer {

            text-align: center;

            color: #777777;

            font-size: 12px;

            padding: 30px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )