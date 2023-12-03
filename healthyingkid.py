import streamlit as st
import pandas as pd
import sqlite3
import datetime
###################################################################################################
# 0. page config & title
st.set_page_config(layout="centered", page_title="AI융합캡스톤디자인과창업-프로토타입", page_icon="🚀")

from streamlit_option_menu import option_menu
selected3 = option_menu(None, ["menu1", "menu2",  "menu3"], 
    icons=['house', 'cloud-upload', "list-task"], 
    menu_icon="cast", default_index=0, orientation="horizontal",key="test_key",
    styles={
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "icon": {"color": "white", "font-size": "13px"}, 
        "nav-link": {"font-size": "13px", "text-align": "center", "margin":"1px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "red"},
    }
)
###################################################################################################
# 1. 현재위치 찾기
import json
import os
import requests
from dotenv import load_dotenv
geo_key = "AIzaSyDycTBtqJ9ZrbXqtR3hNvYTqnTLZ90CwII"
load_dotenv(verbose=True)
map_url = f'https://www.googleapis.com/geolocation/v1/geolocate?key={geo_key}'
map_data = {'considerIp': True,}
map_res = json.loads(requests.post(map_url, map_data).text)
#lat_here, lng_here = map_res["location"]["lat"], map_res["location"]["lng"]
lat_here, lng_here = 37.5509442, 126.9410023
###################################################################################################
# 2. 한국지도 배경
import math
import folium
from streamlit_folium import folium_static
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
# 지도를 생성합니다. 초기 중심점은 서울 시청으로 설정합니다.
vworld_key = "458B8D85-22C4-38EC-896C-772ACC9D16B3"
layer = "Base"
tileType = "png"
tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/{layer}/{{z}}/{{y}}/{{x}}.{tileType}"
###################################################################################################
# 3. 병원 마커 찍기 (미완성)
df = pd.read_csv("https://raw.githubusercontent.com/bangmijung/streamlit-example/master/%EB%B3%91%EC%9B%90%EC%A0%95%EB%B3%B4_%EA%B8%B0%EB%B3%B8.csv")
target_df = df[((df["요양기관명"].str.contains("소아"))|(df["종별코드명"].isin(["상급종합", "종합병원"])))&(df["좌표(Y)"]>(lat_here-0.0091*4))&(df["좌표(Y)"]<(lat_here+0.0091*4))&(df["좌표(X)"]>(lng_here-0.0113*4))&(df["좌표(X)"]<(lng_here+0.0113*4))]

# 3. 병원 마커 찍기 (미완성)
def map_mark(lat_here, lng_here):
    from folium.plugins import MarkerCluster
    m = folium.Map(location=[lat_here, lng_here],tiles=tiles,attr="Vworld", zoom_start=15)
    marker_cluster = MarkerCluster().add_to(m)
    for name, lat, long in (zip(target_df["요양기관명"], target_df["좌표(Y)"], target_df["좌표(X)"])):
        if math.isnan(lat)==False and math.isnan(long)==False:
            iframe = folium.IFrame("<button type=\"button\" onclick=\"window.open('https://map.naver.com/p/search/%EC%86%8C%EC%95%84%EA%B3%BC')\" style=\"width:150px;\">예약페이지로 이동</button>")
            popup = folium.Popup(iframe, min_height=40, max_height=40, min_width=180, max_width=180)
            folium.Marker(
                [lat, long], 
                popup=popup, 
                tooltip=name,
            ).add_to(m)
            
    return m

m = map_mark(lat_here, lng_here)
###################################################################################################
# 4. 병원 세부정보
import json
import xmltodict
import pandas as pd
import requests
def get_medi_info(medi_cd):
    serviceKey = "0uLqFHM%2Be9J%2FbiIOen1q2UD23OWpWIIiFCkXLfl%2BRfdEnVJqIoN6rO18Bx2nucFdU7Cta6bgknn9b6ilI2ll1g%3D%3D"
    if medi_cd is not None:
        url = f"http://apis.data.go.kr/B551182/MadmDtlInfoService2.6/getDtlInfo2.6?serviceKey={serviceKey}&ykiho={medi_cd}&pageNo=1&numOfRows=100&_type=json"
        response = requests.get(url)
        df = pd.DataFrame.from_dict(json.loads(response.text)["response"]["body"]["items"]["item"],orient="index")
        return df
    else:
        return None
    
# 4-1. 병원 세부정보에서 영업시간을 찾아주는 함수
def find_time(medi_info, today):
    import re
    import datetime
    weekday = today.weekday()
    if weekday == 0:
        weekday_en = "Mon"
    elif weekday == 1:
        weekday_en = "Tue"
    elif weekday == 2:
        weekday_en = "Wed"
    elif weekday == 3:
        weekday_en = "Thu"
    elif weekday == 4:
        weekday_en = "Fri"
    elif weekday == 5:
        weekday_en = "Sat"
    elif weekday == 6:
        weekday_en = "Sun"
    # 영업시간
    try:
        if f"trmt{weekday_en}Start" in medi_info.index:
            start = medi_info[0][f"trmt{weekday_en}Start"]
            end = str(medi_info[0][f"trmt{weekday_en}End"])
            start_edited = today.replace(hour=int(start[:2]), minute=int(start[2:]), second=0, microsecond=0)
            end_edited = today.replace(hour=int(end[:2]), minute=int(end[2:]), second=0, microsecond=0)
        else:
            start_edited = None
            end_edited = None
        # 점심시간
        if "lunchWeek" in medi_info.index:
            lunchWeek = medi_info[0]["lunchWeek"]
            pattern = r'(\d{1,2}):(\d{2})|(\d{1,2})시\s?(\d{1,2})분?'
            matches = re.findall(pattern, lunchWeek)
            lunch_start = today.replace(hour=int(matches[0][0]), minute=int(matches[0][1]), second=0, microsecond=0)
            lunch_end = today.replace(hour=int(matches[1][0]), minute=int(matches[1][1]), second=0, microsecond=0)
        else:
            lunch_start = None
            lunch_end = None
        return start_edited, end_edited, lunch_start, lunch_end
    except:
        return None, None, None, None
###################################################################################################
# 주차정보를 찾아주는 함수
def find_parking_info(medi_info):
    try:
        # 주차 가능 대수
        if "parkQty" in medi_info.index:
            parking_qty = medi_info[0]["parkQty"]
        else:
            parking_qty = None
        # 주차비용부담여부 (Y:비용발생, N:무료)
        if "parkXpnsYn" in medi_info.index:
            parking_yn = medi_info[0]["parkXpnsYn"]
        else:
            parking_yn = None
        # 기타안내
        if "parkEtc" in medi_info.index:
            parking_etc = medi_info[0]["parkEtc"]
        else:
            parking_etc = None
        return parking_qty, parking_yn, parking_etc
    except:
        return None, None, None
###################################################################################################
# 4. Menu Item Selection
selection = st.session_state["test_key"]

if selection == None or selection == "menu1":
    # [기능1-가까운 소아병원 찾기]
    st.subheader("🏥 가까운 소아병원 찾기")
    distance = st.select_slider("Set distance",["🏃🏻‍♀️도보이동", "🚘대중교통 이용", "🚗자가용 이용"],label_visibility="collapsed")
    if distance == "🏃🏻‍♀️도보이동":
        zoom_idx=15
    elif distance == "🚘대중교통 이용":
        zoom_idx=13.5
    else:
        zoom_idx=12

    # [지도 그리기]
    st.write("📍현재위치: ", lat_here,lng_here)
    out = st_folium(m,zoom = zoom_idx, width=340, height=300)
    if out["last_object_clicked"] is not None:
        with st.form("test"):
            medi_cd = df[(df["좌표(Y)"]==out["last_object_clicked"]["lat"])&(df["좌표(X)"]==out["last_object_clicked"]["lng"])]["암호화요양기호"].reset_index()["암호화요양기호"][0]
            medi_info = get_medi_info(medi_cd)
            # 클릭한 좌표에 맞는 병원정보
            with st.chat_message("assistant", avatar="🏥"):
                st.write("**"+out["last_object_clicked_tooltip"]+"**")
                st.write("📞 **병원 전화번호:**")
                st.write(df[df["암호화요양기호"]==medi_cd]["전화번호"].item())
                st.write("🧭 **병원 도로명주소:**")
                st.write(df[df["암호화요양기호"]==medi_cd]["주소"].item())
            # 예제1 (영업시작, 영업끝, 점심시작, 점심끝)
            with st.chat_message("assistant", avatar="🕐"):
                st.write(" **영업시간 정보**")
                start_edited, end_edited, lunch_start, lunch_end = find_time(medi_info, datetime.datetime(2023, 12, 4))#find_time(medi_info, datetime.datetime.today())
                if start_edited == None and end_edited == None:
                    st.write("✔ 오늘은 휴무일입니다. 다음에 방문해주세요!")
                else:
                    st.write(f"✔ 오늘의 영업시간은 {start_edited.hour}시 {start_edited.minute} 부터 {end_edited.hour}시 {end_edited.minute}분 까지입니다.")
                    if lunch_start != None and lunch_end != None:
                        st.write(f"✔ 병원의 점심시간은 {lunch_start.hour}시 {lunch_start.minute} 부터 {lunch_end.hour}시 {lunch_end.minute}분 까지입니다.")
 
            # 예제2 (주차장 정보)
            with st.chat_message("assistant", avatar="🚜"):
                st.write(" **주차장 정보:**")
                parking_info = find_parking_info(medi_info)
                st.write("1️⃣ **주차가능대수:** ", parking_info[0])
                if parking_info[1] == "N":
                    st.write("2️⃣ **주차지원여부:** ")
                    st.write("방문자 주차등록 가능")
                else:
                    st.write("2️⃣ **주차지원여부:**")
                    st.write("방문자 주차등록 가능")
                st.write("3️⃣ **주차관련안내:**")
                st.write(parking_info[2])
            st.form_submit_button("👩🏻‍⚕️병원 예약하러 가기", use_container_width=True)

elif selection == "menu2":
    import openai
    import deepl
    #번역기 생성
    DeepL_API_KEY = 'c24af978-e422-0d8b-4420-4c2daa1a067e:fx'
    translator = deepl.Translator(DeepL_API_KEY)
    st.title("우리아이 육아일기 🧒📔")
    tab1, tab2 = st.tabs(["육아일기 쓰기", "육아일기 찾기"])

    # 육아일기 쓰기 탭
    with tab1:
        
        api_key_1=st.text_input("api key를 입력하세요:", key="api_key_1")
        openai.api_key=api_key_1
        st.subheader("✍🏻육아일기 쓰기")
        
        #아이정보 csv 가져오기
        import requests
        import pandas as pd
        
        url = 'https://raw.githubusercontent.com/annayjs/healthyingkid/main/child_info.csv'  # GitHub에 있는 CSV 파일의 URL
        response = requests.get(url)
        open('child_info.csv', 'wb').write(response.content)

        child_data = pd.read_csv('child_info.csv')
        child_name_list=child_data['name'].to_list()

        child_choice = st.radio("아이를 선택하세요:", (child_name_list), key='choice1')
        child_idx=child_name_list.index(child_choice)

        if child_choice is not None:
            gender=child_data[child_data['name']==child_choice]['gender'][child_idx]
            age=child_data[child_data['name']==child_choice]['age'][child_idx]
            height=child_data[child_data['name']==child_choice]['height'][child_idx]
            weight=child_data[child_data['name']==child_choice]['weight'][child_idx]
        
        date = st.date_input("날짜를 선택하세요")
        diary_text = st.text_area("오늘 우리 아이는 어땠나요?")
        submit_button = st.button("저장하기", key='submit1')

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "system", 
                 "content": "You are a pediatrician. Speak like you are a medical specialist"}
            ]

        if submit_button and diary_text:  # 일기 텍스트가 있을 때만 처리
            diary_prompt= """
                %s \n
                위의 글은 부모님이 아이의 건강에 대한 육아일기를 적은 내용이야. 
                아이의 성별은 %s, 키는 %fcm, 몸무게가 %fkg, 나이는 %d살이야.
                육아일기의 내용과, 아이의 정보를 고려해서 이 육아일기에 대한 감정적, 의료적 피드백을 세 항목으로 해줘."""%(diary_text, gender, height, weight, age)
            diary_prompt_eng=translator.translate_text(diary_prompt, target_lang="EN-US").text
            st.session_state.messages.append({"role": "user", 
                                          "content": diary_prompt_eng})
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=st.session_state.messages, 
                max_tokens=200
            )
            answer = translator.translate_text(response.choices[0].message.content, target_lang='KO').text
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.write("오늘의 육아일기:")
            st.write(diary_text)
        
        for message in st.session_state.messages:
            if message["role"] == "assistant":
                gpt_feedback = message['content']
                st.write("_________________________________________________________________________________________________________")
                st.write("👩‍⚕️닥터 아이봇의 육아일기 세 줄 피드백!: ")
                st.write(f"{gpt_feedback}")
                st.write("_________________________________________________________________________________________________________")
                st.success("저장되었습니다!")
    
    # 육아일기 찾기 탭
    with tab2:
        st.subheader("🔍육아일기 찾기")
        view_date = st.date_input("날짜를 선택하세요", key="view_date2")
        #아이정보 csv 가져오기
        import requests
        import pandas as pd
        
        url = 'https://raw.githubusercontent.com/annayjs/healthyingkid/main/child_info.csv'  # GitHub에 있는 CSV 파일의 URL
        response = requests.get(url)
        open('child_info.csv', 'wb').write(response.content)

        child_data = pd.read_csv('child_info.csv')
        child_name_list=child_data['name'].to_list()

        child_choice_2 = st.radio("아이를 선택하세요:", (child_name_list), key='choice2')
        child_idx=child_name_list.index(child_choice_2)

        if child_choice_2 is not None:
            st.write(f"Day 1✏️: \n {child_data[child_data['name']==child_choice_2].loc[:, 'Day 1'][child_idx]}")
            st.write("_________________________________________________________________________________________________________")
            st.write(f"Day 2✏️: \n{child_data[child_data['name']==child_choice_2].loc[:, 'Day 2'][child_idx]}")
            st.write("_________________________________________________________________________________________________________")
            st.write(f"Day 3✏️: \n{child_data[child_data['name']==child_choice_2].loc[:, 'Day 3'][child_idx]}")
            

###################################################################################################################
elif selection == "menu3":
    import streamlit
    import openai
    import deepl
    import csv

    st.title("닥터 아이봇 상담👩‍⚕️")
    api_key=st.text_input("api key를 입력하세요:", key="api_key")
    openai.api_key=api_key
    #번역기 생성
    DeepL_API_KEY = 'c24af978-e422-0d8b-4420-4c2daa1a067e:fx'
    translator = deepl.Translator(DeepL_API_KEY)

    import requests
    import pandas as pd
    
    url = 'https://raw.githubusercontent.com/annayjs/healthyingkid/main/child_info.csv'  # GitHub에 있는 CSV 파일의 URL
    response = requests.get(url)
    open('child_info.csv', 'wb').write(response.content)

    child_data = pd.read_csv('child_info.csv')
    child_name_list=child_data['name'].to_list()

    #아이 선택하기
    child_choice = st.radio("상담할 아이를 선택하세요:", (child_name_list))
    child_idx=child_name_list.index(child_choice)
    

    if child_choice is not None:
        gender=child_data[child_data['name']==child_choice]['gender'][child_idx]
        age=child_data[child_data['name']==child_choice]['age'][child_idx]
        height=child_data[child_data['name']==child_choice]['height'][child_idx]
        weight=child_data[child_data['name']==child_choice]['weight'][child_idx]
        st.subheader("우리 아이 정보🧒ℹ️")
        st.write(f"성별: {gender} 아이 | 나이: {age} 세")
        st.write(f"키: {height} cm | 몸무게: {weight} kg")
        d1=child_data[child_data['name']==child_choice]['Day 1'][child_idx]
        d2=child_data[child_data['name']==child_choice]['Day 2'][child_idx]
        d3=child_data[child_data['name']==child_choice]['Day 3'][child_idx]
        
    
    with st.form("chat_form", clear_on_submit=True):
        symptom = st.text_input("상담 내용을 입력하세요:", key="user_input")
        submitted = st.form_submit_button("입력")
    
    st.subheader("📝 상담 로그")
    st.write("_________________________________________________________________________________________________________")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", 
             "content": "You are a pediatrician. Speak like you are a medical specialist"}
        ]
    
    if submitted and symptom:
        prompt= """
                의료와 관련된 질문을 할 거야. 성인이 아닌 소아나 청소년이라는 점을 고려해서 답변해줘!
                아이의 성별은 %s, 키는 %fcm, 몸무게가 %fkg, 나이는 %d살이야.
                
                최근 3일 간 아이가 보인 특징은 다음과 같아.
                - 3일전: %s
                - 2일전: %s
                - 1일전: %s
    
                현재 상황은 다음과 같아.
                - %s
                
                위의 모든 정보를 고려해서 맞춤 치료방법과 복용해야하는 약 등 아이의 건강 상태를 진단해줘."""%(gender, height, weight, age, d1, d2, d3, symptom)
        prompt_eng=translator.translate_text(prompt, target_lang="EN-US").text
        st.session_state.messages.append({"role": "user", 
                                      "content": prompt_eng})
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=st.session_state.messages, 
            max_tokens=1000
        )
        answer = translator.translate_text(response.choices[0].message.content, target_lang='KO').text
        st.session_state.messages.append({"role": "assistant", "content": answer + "@@@" + symptom})
        
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            gpt_answer = message['content'].split('@@@')[0]
            input_symptom = message['content'].split('@@@')[1]
            st.write("🙋‍♂나:")
            st.write(symptom)
            st.write("_________________________________________________________________________________________________________")
            st.write("👩‍⚕️닥터 아이봇: ")
            st.write(f"{gpt_answer}")
            st.write("_________________________________________________________________________________________________________")
            

