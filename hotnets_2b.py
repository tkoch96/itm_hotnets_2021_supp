import matplotlib.pyplot as plt, numpy as np, csv
from sklearn.linear_model import LinearRegression


### DATA LOADING
# Load APNIC Data
apnic_data, i =  {}, 0
with open("aspop", 'r') as f:
	for row in f:
		i+=1
		if i == 1: continue
		fields = row.strip().split(',')
		asn = int(fields[0])
		users = int(fields[2])
		try:
			apnic_data[asn] += users
		except KeyError:
			apnic_data[asn] = users

# ASN -> ISP mappings for ISPs from PeeringDB
isp_to_asn = {
	"Orange":[3215], "Bouygues": [5410], "Free": [12322],
	"Free_M": [51207], "SFR": [15557,8228,21502], "El_tele":[25117],
	"Comcast": [7922, 33654,7725,33665,33657,33667,33491,33652,33659,33287,
		33662,33655,33489,33656,22258,20214,33668,13367,22909,7015,33653,7016,33490], 
	"Charter": [20115,10796,20001, 11351, 11426, 11427, 12271], 
	"Cox": [22773], "Altice": [6128],
	"MediaCom": [30036], "BT": [5400], "Sky Broadband": [5607], "Virgin Media": [5089],
	"TalkTalk": [9105], "KDDI": [2516], "NTT": [4713, 9605], "SoftBank": [17676], "JCOM": [9824],
	"KoreaTelecom": [4766], "SKTelecom": [9318, 9644], "LG": [17858, 17853, 3786]
}
asn_to_isp = {}
for isp in isp_to_asn:
	for asn in isp_to_asn[isp]:
		asn_to_isp[asn] = isp
isp_apnic_users = {k:0 for k in isp_to_asn}
# Count APNIC users per ISP (which may include users from several ASNs)
for isp in isp_to_asn:
	for asn in isp_to_asn[isp]:
		try:
		 isp_apnic_users[isp] += apnic_data[asn]
		except KeyError:
			pass

# ASN to hit counts
all_gpdns_probing_count_data = list(csv.DictReader(open("gpdns_hit_counts.csv", 'r')))
isp_gpdns_hit_counts = {isp:[0,0] for isp in isp_to_asn}
for el in all_gpdns_probing_count_data:
	if el['asn'] == '': continue
	asn = int(el['asn'])
	try:
		isp = asn_to_isp[asn]
	except KeyError:
		continue
	isp_gpdns_hit_counts[isp][0] += int(el['total_hits'])
# ASN to hit rates
all_gpdns_probing_rate_data = list(csv.DictReader(open("gpdns_hit_rates.csv", 'r')))
isp_gpdns_hit_rates = {isp:[[],[]] for isp in isp_to_asn}
for el in all_gpdns_probing_rate_data:
	if el['asn'] == '': continue
	asn = int(el['asn'])
	try:
		isp = asn_to_isp[asn]
	except KeyError:
		continue
	isp_gpdns_hit_rates[isp][0].append(float(el['avg_hit_rate']))
	# corresponding counts
	counts = [float(_el['total_hits']) for _el in all_gpdns_probing_count_data if int(_el['asn']) == asn][0]
	if float(el['avg_hit_rate']) > 0:
		isp_gpdns_hit_rates[isp][1].append(counts/float(el['avg_hit_rate']))
	else:
		isp_gpdns_hit_rates[isp][1].append(0)
# Calculate a weighted
for isp in isp_gpdns_hit_rates:
	weights = np.array(isp_gpdns_hit_rates[isp][1])
	rates = np.array(isp_gpdns_hit_rates[isp][0])
	if sum(weights) > 0:
		isp_gpdns_hit_rates[isp][0] = np.average(rates,weights=weights)
	else:
		isp_gpdns_hit_rates[isp] = [0]

# Subscriber counts according to various sources
# FR, US, UK, JP, KR
subscriber_counts = { # Millions, I chose ISPs with more than 1M subscribers
	"Orange": 46.626, # collaborator
	"Bouygues": 22.503, # collaborator
	"Free": 6.671, # collaborator
	"Free_M": 13.476, # collaborator
	"SFR": 22.276, # collaborator
	"El_tele": 2, # collaborator
	"Comcast": 30.6, # https://www.leichtmanresearch.com/about-4860000-added-broadband-from-top-providers-in-2020/
	"Charter": 28.879, # https://www.leichtmanresearch.com/about-4860000-added-broadband-from-top-providers-in-2020/
	"Cox": 5.38, # https://www.leichtmanresearch.com/about-4860000-added-broadband-from-top-providers-in-2020/
	"Altice": 4.3592, # https://www.leichtmanresearch.com/about-4860000-added-broadband-from-top-providers-in-2020/
	"MediaCom": 1.438, # https://www.leichtmanresearch.com/about-4860000-added-broadband-from-top-providers-in-2020/
	"BT": 9.3, # https://www.ispreview.co.uk/review/top10.php
	"Sky Broadband": 6.2, # https://www.ispreview.co.uk/review/top10.php
	"Virgin Media": 5.4941, # https://www.ispreview.co.uk/review/top10.php
	"TalkTalk": 4.2, # https://www.ispreview.co.uk/review/top10.php
	"KDDI": 32.108, # https://www.kddi.com/extlib/files/english/corporate/ir/library/presentation/2022/pdf/kddi_210730_e_data_69pj8d.pdf
	"NTT": 105.11, # Using total from 5G, LTE (Xi), FLET'S Hikari (including Hikari Collaboration Model), (including) Hikari Collaboration Model	https://group.ntt/en/ir/fin/subscriber.html
	"SoftBank": 34.359, # https://www.softbank.jp/en/corp/ir/financials/kpi/
	"JCOM": 5.59, # https://www.jcom.co.jp/corporate_en/aboutus/profile.html
	"KoreaTelecom": 31.96, # https://corp.kt.com/eng/attach/irdata/10454/2Q21%20KT%20NDR%20PT%20ENG_FF.pdf
	"SKTelecom": 37.86, # https://www.sktelecom.com/img/eng/presen/20210203/4Q20InvestorBriefingENG.pdf
	"LG": 21.82, # https://www.uplus.co.kr/cmg/engl/inre/peir/RetrievePeIrIiQuaterList.hpi#
}

# Organize arrays for plotting
ordered_isps = list(isp_to_asn.keys())
subscriber_counts_plot = np.array([subscriber_counts[k] for k in ordered_isps])
isp_gpdns_hits = [isp_gpdns_hit_rates[isp][0] for isp in ordered_isps]
cache_hit_rates_plot = np.array(isp_gpdns_hits)
isp_apnic_users = [isp_apnic_users[k] for k in ordered_isps]
apnic_plot = np.array(isp_apnic_users) / 1000 ** 2

cache_hit_rates_plot = np.reshape(cache_hit_rates_plot, (len(cache_hit_rates_plot), 1))
apnic_plot = np.reshape(apnic_plot, (len(apnic_plot), 1))

### Generating the figure for the paper
fontsize = 24
plt.rcParams['legend.title_fontsize'] = fontsize
fig = plt.figure(figsize=(12, 7))
ax1 = fig.add_subplot(111)
ax2 = ax1.twiny()
max_x_bot = 8 # percent
max_x_top = 30 # million

ln1 = ax1.scatter(cache_hit_rates_plot, subscriber_counts_plot, marker='o', s=70, c='b')
m = LinearRegression(fit_intercept=False).fit(cache_hit_rates_plot, subscriber_counts_plot) # model is y = a x (no intercept)
slope = m.coef_[0]
r = m.score(cache_hit_rates_plot, subscriber_counts_plot)
intercept = 0
ln2 = ax1.plot(np.linspace(0, max_x_bot), slope * np.array(np.linspace(0, max_x_bot)) + intercept, 'b-', label="Cache Hit Rate")

ln3 = ax2.scatter(apnic_plot, subscriber_counts_plot, marker='x', s=70, c='r')
m_a = LinearRegression(fit_intercept=False).fit(apnic_plot, subscriber_counts_plot) # model is y = a x (no intercept)
slope_a = m_a.coef_[0]
r_a = m_a.score(apnic_plot, subscriber_counts_plot)
intercept_a = 0
ln4 = ax2.plot(np.linspace(0, max_x_top), slope_a * np.array(np.linspace(0, max_x_top)) + intercept_a, 'r--',
			label="APNIC Users")

n_ticks = 6
ax1.set_xlim(0.0, max_x_bot)
ax1.set_xticks([round(el,1) for el in np.linspace(0, max_x_bot, num=n_ticks)])
ax1.set_xticklabels([round(el,1) for el in np.linspace(0, max_x_bot, num=n_ticks)], fontsize=fontsize)

ax2.set_xlim(0, max_x_top)
ax2.set_xticks([round(el,1) for el in np.linspace(0, max_x_top, num=n_ticks)])
ax2.set_xticklabels([round(el,1) for el in np.linspace(0, max_x_top, num=n_ticks)], fontsize=fontsize)

y_ticks = [round(el,2) for el in np.linspace(0, 120, num=n_ticks)]
ax1.set_ylim(0, 120)
ax1.set_yticks(y_ticks)
ax1.set_yticklabels(y_ticks, fontsize=fontsize)

ax1.grid(True)
ax2.grid(True)

ax1.set_xlabel("Cache Hit Rate (%) ($\\bullet$)", fontsize=fontsize, c='b')
ax2.set_xlabel("APNIC Estimated Users (M) ($\\times$)", fontsize=fontsize, c='r')
ax1.set_ylabel("Subscribers (M)", fontsize=fontsize)
lns = ln4 + ln2
labs = [l.get_label() for l in lns]
ax1.legend(lns, labs, fontsize=fontsize-2, title="Fitted Lines", loc="upper left")

plt.savefig("subscribers_hitrate_apnic_comparison.pdf", bbox_inches='tight')