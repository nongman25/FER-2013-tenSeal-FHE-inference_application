"""
Client-side diagnosis logic for Streamlit.
Analyzes decrypted statistics and renders a report.
"""
import numpy as np
import scipy.special
import streamlit as st
from typing import List, Union

# FER-2013 데이터셋 감정 라벨
EMOTIONS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

class MentalHealthDiagnostics:
    def __init__(self, depression_th=8.0, instability_th=150.0):
        # 임계값 설정
        self.TH_DEPRESSION = depression_th   
        self.TH_INSTABILITY = instability_th 

    def analyze_and_render(self, plain_sum: Union[List[float], np.ndarray], plain_vol: Union[List[float], np.ndarray], days: int = 10):
        """
        복호화된 평문 데이터를 분석하여 Streamlit UI에 진단 리포트를 그립니다.
        """
        # 입력 데이터 변환
        plain_sum = np.array(plain_sum)
        plain_vol = np.array(plain_vol)

        # 1. 통계 처리
        # 주의: 0으로 나누기 방지
        safe_days = max(days, 1)
        mean_logits = plain_sum / safe_days
        
        # Softmax로 확률 변환
        probs = scipy.special.softmax(mean_logits) * 100 
        
        # 불안정성 점수 (일평균 변동성)
        instability_score = np.sum(plain_vol) / safe_days 
        
        # 2. 주요 감정 추출
        dominant_idx = np.argmax(mean_logits)
        dominant_emotion = EMOTIONS[dominant_idx]
        dominant_intensity = mean_logits[dominant_idx]

        # 3. 진단 로직 (Diagnostic Logic)
        status = "✅ 정상 (Stable)"
        advice = "현재 감정 상태가 안정적입니다."
        status_color = "green" # UI용 색상
        
        # Rule A: 양극성 장애(조울증) 의심
        if instability_score > self.TH_INSTABILITY:
            status = "🚨 양극성 장애 위험 (Bipolar Risk)"
            advice = "감정 기복이 매우 심합니다. 기분 변화(Mood Swings)가 급격합니다."
            status_color = "red"
            
        # Rule B: 우울증 의심
        elif dominant_emotion == 'Sad' and dominant_intensity > self.TH_DEPRESSION:
            status = "⚠️ 우울증 위험 (Depression Risk)"
            advice = "깊은 우울감이 지속되고 있습니다. 감정의 관성(Inertia)이 강합니다."
            status_color = "orange"

        # --- 4. Streamlit 리포트 출력 ---
        st.markdown("---")
        st.subheader("🧠 FHE 기반 정신건강 분석 리포트")
        
        # 결과 요약
        if status_color == "green":
            st.success(f"**진단 결과:** {status}")
        elif status_color == "orange":
            st.warning(f"**진단 결과:** {status}")
        else:
            st.error(f"**진단 결과:** {status}")
            
        st.info(f"💡 **상세 소견:** {advice}")

        # 주요 지표 (컬럼으로 분리)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("분석 기간", f"{days}일")
        with col2:
            st.metric("주요 감정", f"{dominant_emotion}", delta=f"강도 {dominant_intensity:.2f}")
        with col3:
            st.metric("감정 기복도", f"{instability_score:.2f}", delta=f"기준 {self.TH_INSTABILITY}", delta_color="inverse")

        # 감정 분포 차트
        st.markdown("#### 📊 기간 내 평균 감정 분포")
        chart_data = {"Emotion": EMOTIONS, "Probability (%)": probs}
        st.bar_chart(chart_data, x="Emotion", y="Probability (%)")