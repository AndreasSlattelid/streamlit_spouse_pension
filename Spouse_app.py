import pandas as pd
import numpy as np
import k13
import io
import streamlit as st

import plotly.express as px

from siuba import _, gather

st.title("Spouse Pension using K13")

Y = st.sidebar.number_input(
    "Calculation year (Y)", value = 2022, step = 1
)

r = st.sidebar.number_input(
    "Interest rate (r)", value=0.03, step=0.01
)

T = st.sidebar.number_input(
    "Length of contract (T)", max_value=120, value=80, step= 1
)

P = st.sidebar.number_input(
    "Desired Pension (P)", max_value=10**(6), value=10**(5), step=10000
)

submit_button = st.sidebar.button(
    "Submit"
)


c1, c2 = st.columns((2, 2))
genders = ["M", "F"]

with st.container():
    G_p1 = c1.radio("Gender person One:", genders, index=0)
    age_p1 = c1.number_input("Age person One", max_value=120, value=25)
    st.markdown("***")


with st.container():
    G_p2 = c2.radio("Gender person Two:", genders, index=1)
    age_p2 = c2.number_input("Age person Two:", max_value=120, value=24)


def validate_input():
    no_errors = True

    if Y < 2013:
        st.write("Please choose Y >= 2013")
        no_errors = False
    
    if T < 0:
        st.write("Please choose T > 0")
        no_errors = False

    if P < 0:
        st.write("Please choose a pension P >= 0")
        no_errors = False

    if age_p1 < 16:
        st.write("Please choose Age person One >= 16")
        no_errors = False

    if age_p2 < 16:
        st.write("Please choose Age person Two >= 16")
        no_errors = False
    
    if G_p1 not in genders:
        st.write("Please choose Gender person One equal to 'M' or 'F'")
        no_errors = False

    if G_p2 not in genders:
        st.write("Please choose Gender person Two equal to 'M' or 'F'")
        no_errors = False
    

    return no_errors

# States:
  # p1: person aged x
  # p2: person aged y
  # 0: p1, p2 alive
  # 1: p1 deceased, p2 alive
  # 2: p1 alive, p2 deceased
  # 3: p1, p2 deceased

# remaining in state: 0

#--------------------------------------------------------------------------------------------------------#


def v(t):
    # discount factor
    return np.exp(-r*t)


def p_00(t: float, n: int) -> float:
    p1_survive = k13.p_surv(x=age_p1, G=G_p1, Y=Y, t=t, s=n)
    p2_survive = k13.p_surv(x=age_p2, G=G_p2, Y=Y, t=t, s=n)

    return round(p1_survive*p2_survive, 4)


def p_01(t, n):
    p1_die = (1-k13.p_surv(x=age_p1, G=G_p1, Y=Y, t=t, s=n))
    p2_survive = k13.p_surv(x=age_p2, G=G_p2, Y=Y, t=t, s=n)

    return round(p1_die*p2_survive, 4)


def p_02(t, n):
    p1_survive = k13.p_surv(x=age_p1, G=G_p1, Y=Y, t=t, s=n)
    p2_die = (1 - k13.p_surv(x=age_p2, G=G_p2, Y=Y, t=t, s=n))

    return round(p1_survive*p2_die, 4)


def p_11(t, n):
    # p2 remains alive
    p2_survive = k13.p_surv(x=age_p2, G=G_p2, Y=Y, t=t, s=n)

    return round(p2_survive, 4)


def p_22(t, n):
    # p1 remains alive
    p1_survive = k13.p_surv(x=age_p1, G=G_p1, Y=Y, t=t, s=n)

    return round(p1_survive, 4)


#-----------------------------------------------------------#
# Premium calculation:


def prem_upper_summand(n):
    prob = p_01(0, n) + p_02(0, n)
    return v(n)*prob


def prem_lower_summand(n):
    return v(n)*p_00(0, n)



def V_0(t: float) -> float:

    def summand_1(t, n):
        return (v(n)/v(t))*p_00(t, n)

    def summand_2(t, n):
        return (v(n)/v(t))*(p_01(t, n) + p_02(t, n))

    contract_length = np.arange(t, T, 1)

    sum1 = sum((summand_1(t, i) for i in contract_length))
    sum2 = sum((summand_2(t, i) for i in contract_length))

    ans = (-1)*premium_yearly*sum1 + P*sum2
    return (ans)

def V_1(t: float) -> float:

    def summand(t, n):
        return (v(n)/v(t))*p_11(t, n)

    contract_length = np.arange(t, T, 1)

    ans = P*sum((summand(t, i) for i in contract_length))

    return ans


def V_2(t: float) -> float:

    def summand(t, n):
        return (v(n)/v(t))*p_22(t, n)

    contract_length = np.arange(t, T, 1)

    ans = P*sum((summand(t, i) for i in contract_length))

    return (ans)




#buffer = io.BytesIO()

#with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
#    worksheet = df_reserve.to_excel(writer, index=False, sheet_name= "Reserve")
#    writer.save()


#dwnl_button = st.sidebar.download_button(
#        label="Download Excel",
#        data=buffer,
#        file_name="reserve.xlsx",
#        mime="application/vnd.ms-excel",
#        on_click= st.dataframe(df_reserve)
#    )

if submit_button and validate_input():

    # Contract lasts from 0 to T - 1, I need to be careful: indexing starts at 0 in python.
    length_contract = np.arange(0, T, 1)

    prem_above_expr = P*sum(list(map(prem_upper_summand, length_contract)))
    prem_below_expr = sum(list(map(prem_lower_summand, length_contract)))

    premium_yearly = prem_above_expr/prem_below_expr

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.text(
                f"The yearly premium should be NOK: {round(premium_yearly)}")
        with col2:
            st.text(
                f"The monthly premium should be NOK: {round(premium_yearly/12)}")

    reserve_0 = pd.Series(list(map(V_0, length_contract)))

    reserve_1 = pd.Series(list(map(V_1, length_contract)))

    reserve_2 = pd.Series(list(map(V_2, length_contract)))

    reserve = {"length_contract": length_contract, "reserve_state0": reserve_0,
               "reserve_state1": reserve_1, "reserve_state2": reserve_2}

    df_reserve = pd.DataFrame(reserve)

    # dplyr syntax as I love this way of data wrangeling:
    df_plt = df_reserve >> gather("reserve_state", "value", _["reserve_state0":"reserve_state2"])

    fig_reserve = px.line(df_plt, x="length_contract",
                        y="value",
                        color="reserve_state",
                        labels={
                            "length_contract": "Contract period (Years)",
                            "value": "Reserve",
                            "reserve_state": "Reserve in states"
                        },
                        hover_data={'value':':.0f'}, 
                        title="Overview reserve")

    st.dataframe(df_reserve)
    st.plotly_chart(fig_reserve)