import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

# إعدادات الصفحة
st.set_page_config(
    page_title="نظام إدارة المخبز - تحكم الأسعار المخصص",
    page_icon="🥖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ملفات حفظ البيانات
SETTINGS_FILE = "bakery_settings_v3.json"

# دالة لحفظ الإعدادات
def save_settings():
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.settings, f, ensure_ascii=False, indent=4)

# دالة لتحميل الإعدادات
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # إعدادات افتراضية
    default_distributors = ["هيثم", "وجيه", "المفرش", "علي", "درهم", "كاش"]
    return {
        'units_per_bag': 1600,
        'distributor_prices': {d: 16 for d in default_distributors},
        'other_prices': {
            'روتي طويل': 50,
            'كيك': 100,
            'خبز': 30,
            'فحم': 200
        },
        'costs': {
            'labor': 53000,
            'wood': 20000,
            'misc_per_bag': 1000
        },
        'distributors': default_distributors
    }

# تصميم CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; }
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .dist-card { background-color: white; padding: 20px; border-radius: 10px; margin-bottom: 10px; border-right: 5px solid #e67e22; }
    section[data-testid="stSidebar"] { background-color: #1e293b; color: white; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# تهيئة الحالة
if 'settings' not in st.session_state:
    st.session_state.settings = load_settings()

if 'daily_data' not in st.session_state:
    st.session_state.daily_data = {
        'date': datetime.now().strftime("%Y-%m-%d"),
        'flour_bags': 0,
        'distribution': {d: {'delivered': 0, 'returned': 0, 'paid': 0} for d in st.session_state.settings['distributors']},
        'other_sales': {k: 0 for k in st.session_state.settings['other_prices'].keys()}
    }

# القائمة الجانبية
with st.sidebar:
    st.title("🥖 إدارة المخبز")
    st.markdown(f"📅 اليوم: {st.session_state.daily_data['date']}")
    menu = st.radio("القائمة:", ["📊 لوحة التحكم", "🍞 الإنتاج", "🚚 الموزعين والأسعار", "🍪 مبيعات أخرى", "⚙️ الإعدادات العامة"])
    st.divider()
    if st.button("💾 حفظ البيانات"):
        st.success("تم الحفظ بنجاح")

# --- 1. لوحة التحكم ---
if menu == "📊 لوحة التحكم":
    st.header("📊 ملخص الحسابات اليومية")
    
    s = st.session_state.settings
    d_data = st.session_state.daily_data
    
    # الحسابات المالية
    expected_prod = d_data['flour_bags'] * s['units_per_bag']
    
    rev_dist = 0
    total_units_sold = 0
    for d in s['distributors']:
        if d in d_data['distribution']:
            net = d_data['distribution'][d]['delivered'] - d_data['distribution'][d]['returned']
            price = s['distributor_prices'].get(d, 16)
            rev_dist += net * price
            total_units_sold += net
            
    rev_others = sum(d_data['other_sales'][k] * s['other_prices'][k] for k in s['other_prices'])
    
    total_revenue = rev_dist + rev_others
    total_expenses = s['costs']['labor'] + s['costs']['wood'] + (d_data['flour_bags'] * s['costs']['misc_per_bag'])
    
    deficit = expected_prod - total_units_sold
    # حساب قيمة العجز بناءً على متوسط سعر الموزعين أو سعر افتراضي
    avg_price = sum(s['distributor_prices'].values()) / len(s['distributor_prices']) if s['distributor_prices'] else 16
    loss_val = max(0, deficit * avg_price)
    
    net_profit = total_revenue - total_expenses - loss_val

    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي الإيرادات", f"{total_revenue:,.0f}")
    c2.metric("إجمالي المصروفات", f"{total_expenses:,.0f}")
    c3.metric("صافي الربح", f"{net_profit:,.0f}")

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📈 حالة الإنتاج")
        st.write(f"الإنتاج المتوقع: **{expected_prod:,}**")
        st.write(f"المبيعات الفعلية: **{total_units_sold:,}**")
        if deficit > 0:
            st.error(f"العجز: {deficit:,} وحدة")
            st.error(f"قيمة الخسارة: {loss_val:,.0f} ريال")
    with col_b:
        st.subheader("💰 التحصيل والديون")
        total_paid = sum(d_data['distribution'][d]['paid'] for d in s['distributors'] if d in d_data['distribution'])
        st.write(f"إجمالي الكاش المستلم: **{total_paid + rev_others:,.0f}**")
        st.warning(f"الديون الجديدة اليوم: **{rev_dist - total_paid:,.0f}**")

# --- 2. الإنتاج ---
elif menu == "🍞 الإنتاج":
    st.header("🍞 مدخلات الإنتاج")
    st.session_state.daily_data['flour_bags'] = st.number_input("عدد أكياس الدقيق", min_value=0, value=st.session_state.daily_data['flour_bags'])
    st.info(f"الإنتاج المتوقع: {st.session_state.daily_data['flour_bags'] * st.session_state.settings['units_per_bag']:,} روتي")

# --- 3. الموزعين والأسعار ---
elif menu == "🚚 الموزعين والأسعار":
    st.header("🚚 توزيع المبيعات (تحكم فردي بالأسعار)")
    
    s = st.session_state.settings
    for d in s['distributors']:
        if d not in st.session_state.daily_data['distribution']:
            st.session_state.daily_data['distribution'][d] = {'delivered': 0, 'returned': 0, 'paid': 0}
        
        # التأكد من وجود سعر للموزع في الإعدادات
        if d not in s['distributor_prices']:
            s['distributor_prices'][d] = 16

        with st.container():
            st.markdown(f"<div class='dist-card'>", unsafe_allow_html=True)
            st.subheader(f"👤 الموزع: {d}")
            
            # صف التحكم بالسعر والكميات
            col_p, col_d, col_r, col_c = st.columns([1, 1.5, 1.5, 1.5])
            with col_p:
                # ميزة التحكم في السعر لكل واحد على حدة
                new_price = st.number_input(f"السعر ({d})", min_value=0, value=s['distributor_prices'][d], key=f"p_{d}")
                if new_price != s['distributor_prices'][d]:
                    s['distributor_prices'][d] = new_price
                    save_settings()
            
            with col_d:
                st.session_state.daily_data['distribution'][d]['delivered'] = st.number_input(f"المسلم", min_value=0, value=st.session_state.daily_data['distribution'][d]['delivered'], key=f"del_{d}")
            with col_r:
                st.session_state.daily_data['distribution'][d]['returned'] = st.number_input(f"المرتجع", min_value=0, value=st.session_state.daily_data['distribution'][d]['returned'], key=f"ret_{d}")
            with col_c:
                st.session_state.daily_data['distribution'][d]['paid'] = st.number_input(f"المدفوع كاش", min_value=0, value=st.session_state.daily_data['distribution'][d]['paid'], key=f"paid_{d}")
            
            # الحسابات الفورية للموزع
            net = st.session_state.daily_data['distribution'][d]['delivered'] - st.session_state.daily_data['distribution'][d]['returned']
            total_due = net * s['distributor_prices'][d]
            balance = total_due - st.session_state.daily_data['distribution'][d]['paid']
            
            st.markdown(f"**الصافي:** {net} وحدة | **الإجمالي المستحق:** {total_due:,.0f} ريال | **المتبقي (دين):** <span style='color:{'red' if balance > 0 else 'green'}'>{balance:,.0f} ريال</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# --- 4. مبيعات أخرى ---
elif menu == "🍪 مبيعات أخرى":
    st.header("🍪 مبيعات الأصناف الإضافية")
    s = st.session_state.settings
    for item in s['other_prices']:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.session_state.daily_data['other_sales'][item] = st.number_input(f"كمية {item}", min_value=0, value=st.session_state.daily_data['other_sales'][item])
        with col2:
            # التحكم في سعر الأصناف الأخرى أيضاً
            new_p = st.number_input(f"سعر {item}", min_value=0, value=s['other_prices'][item], key=f"op_{item}")
            if new_p != s['other_prices'][item]:
                s['other_prices'][item] = new_p
                save_settings()
        st.divider()

# --- 5. الإعدادات العامة ---
elif menu == "⚙️ الإعدادات العامة":
    st.header("⚙️ إعدادات النظام")
    s = st.session_state.settings
    
    with st.form("gen_settings"):
        st.subheader("التكاليف والإنتاجية")
        col1, col2 = st.columns(2)
        with col1:
            s['units_per_bag'] = st.number_input("عدد الوحدات لكل كيس", value=s['units_per_bag'])
            s['costs']['labor'] = st.number_input("تكلفة العمالة اليومية", value=s['costs']['labor'])
        with col2:
            s['costs']['wood'] = st.number_input("تكلفة الحطب اليومية", value=s['costs']['wood'])
            s['costs']['misc_per_bag'] = st.number_input("مصاريف أخرى لكل كيس", value=s['costs']['misc_per_bag'])
        
        st.subheader("إدارة الموزعين")
        dist_text = st.text_area("قائمة الموزعين (مفصولين بفاصلة)", value=", ".join(s['distributors']))
        
        if st.form_submit_button("حفظ الإعدادات العامة"):
            new_dists = [d.strip() for d in dist_text.split(",") if d.strip()]
            s['distributors'] = new_dists
            # إضافة أسعار افتراضية للموزعين الجدد
            for d in new_dists:
                if d not in s['distributor_prices']:
                    s['distributor_prices'][d] = 16
            st.session_state.settings = s
            save_settings()
            st.success("تم تحديث الإعدادات بنجاح!")
