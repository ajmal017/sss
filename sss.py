import time
import pandas   as pd
import yfinance as yf
import csv
import os
import itertools
import sss_filenames
import investpy

from threading import Thread
from dataclasses import dataclass


@dataclass
class StockData:
    ticker:                            str   = 'None'
    short_name:                        str   = 'None'
    quote_type:                        str   = 'None'
    sector:                            str   = 'None'
    sss_value:                         float = 0.0
    ssss_value:                        float = 0.0
    sssss_value:                       float = 0.0
    ssse_value:                        float = 0.0
    sssse_value:                       float = 0.0
    ssssse_value:                      float = 0.0
    sssi_value:                        float = 0.0
    ssssi_value:                       float = 0.0
    sssssi_value:                      float = 0.0
    sssei_value:                       float = 0.0
    ssssei_value:                      float = 0.0
    sssssei_value:                     float = 0.0
    enterprise_value_to_revenue:       float = 0.0
    trailing_price_to_earnings:        float = 0.0
    enterprise_value_to_ebitda:        float = 0.0
    profit_margin:                     float = 0.0
    held_percent_institutions:         float = 0.0
    forward_eps:                       float = 0.0
    trailing_eps:                      float = 0.0
    price_to_book:                     float = 0.0
    shares_outstanding:                float = 0.0
    net_income_to_common_shareholders: float = 0.0
    nitcsh_to_shares_outstanding:      float = 0.0
    num_employees:                     int   = 0
    enterprise_value:                  int   = 0
    nitcsh_to_num_employees:           float = 0.0
    earnings_quarterly_growth:         float = 0.0
    price_to_earnings_to_growth_ratio: float = 0.0
    last_4_dividends_0:                float = 0.0
    last_4_dividends_1:                float = 0.0
    last_4_dividends_2:                float = 0.0
    last_4_dividends_3:                float = 0.0

# Working Mode:
BUILD_CSV_DB                      = 0
CSV_DB_PATH                       = 'Results/20201030-080126'
READ_UNITED_STATES_INPUT_SYMBOLS  = 0            # when set, covers 7,000 stocks
TASE_MODE                         = 0            # Work on the Israeli Market only
NUM_THREADS                       = 1            # 1..5 Threads are supported
FORWARD_EPS_INCLUDED              = 1
MARKET_CAP_INCLUDED               = 1

# Working Parameters:
MIN_ENTERPRISE_VALUE              = 500000000    # In $
NUM_EMPLOYEES_UNKNOWN             = 10000000     # This will make the company very inefficient in terms of number of employees
MUTUALFUND                        = 'MUTUALFUND' # Definition of a mutual fund 'quoteType' field in base.py, those are not interesting
PROFIT_MARGIN_UNKNOWN             = 0.025        # This will make the company not profitable terms of profit margins, thus less attractive
PROFIT_MARGIN_LIMIT               = (0.175 + 0.075 * READ_UNITED_STATES_INPUT_SYMBOLS) / (1 + 2 * TASE_MODE)
PERCENT_HELD_INSTITUTIONS_LOW     = 0.01         # low, to make less relevant
PEG_UNKNOWN                       = 10           # use a rather high value, such that those companies with PEG - will be more attractive since the information exists for them
SHARES_OUTSTANDING_UNKNOWN        = 100000000    # 100 Million Shares - just a value for calculation of a currently unused vaue
EARNINGS_QUARTERLY_GROWTH_MIN     = -0.125*TASE_MODE       # The earnings can decrease by 1/8, but there is still a requirement that price_to_earnings_to_growth_ratio > 0
NUM_ROUND_DECIMALS                = 4
BEST_N_SELECT                     = 50                     # Select best N from each of the resulting sorted tables
ENTERPRISE_VALUE_TO_REVENUE_LIMIT = 17.5 - 2.5 * READ_UNITED_STATES_INPUT_SYMBOLS - 2.5 * TASE_MODE                    # Higher than that is too expensive
SECTORS_LIST                      = [] # ['Technology', 'Consumer Cyclical', 'Consumer Defensive', 'Industrials', 'Consumer Goods']  # Allows filtering by sector(s)
BAD_SSS                           = 10.0**10.0
BAD_SSSE                          = 0


if len(SECTORS_LIST):
    ENTERPRISE_VALUE_TO_REVENUE_LIMIT *= 5
    PROFIT_MARGIN_LIMIT               /= 3

payload            = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies') # There are 2 tables on the Wikipedia page, get the first table
first_table        = payload[0]
second_table       = payload[1]
df                 = first_table
symbols_snp500     = df['Symbol'].values.tolist()
symbols_nasdaq100  = ['ATVI', 'ADBE', 'AMD', 'ALXN', 'ALGN', 'GOOG', 'GOOGL', 'AMZN', 'AMGN', 'ADI', 'ANSS', 'AAPL', 'AMAT', 'ASML', 'ADSK', 'ADP', 'BIDU', 'BIIB', 'BMRN', 'BKNG', 'AVGO', 'CDNS', 'CDW', 'CERN', 'CHTR', 'CHKP', 'CTAS', 'CSCO', 'CTXS', 'CTSH', 'CMCSA', 'CPRT', 'COST', 'CSX', 'DXCM', 'DOCU', 'DLTR', 'EBAY', 'EA', 'EXC', 'EXPE', 'FB', 'FAST', 'FISV', 'FOX', 'FOXA', 'GILD', 'IDXX', 'ILMN', 'INCY', 'INTC', 'INTU', 'ISRG', 'JD', 'KLAC', 'LRCX', 'LBTYA', 'LBTYK', 'LULU', 'MAR', 'MXIM', 'MELI', 'MCHP', 'MU', 'MSFT', 'MRNA', 'MDLZ', 'MNST', 'NTES', 'NFLX', 'NVDA', 'NXPI', 'ORLY', 'PCAR', 'PAYX', 'PYPL', 'PEP', 'PDD', 'QCOM', 'REGN', 'ROST', 'SGEN', 'SIRI', 'SWKS', 'SPLK', 'SBUX', 'SNPS', 'TMUS', 'TTWO', 'TSLA', 'TXN', 'KHC', 'TCOM', 'ULTA', 'VRSN', 'VRSK', 'VRTX', 'WBA', 'WDC', 'WDAY', 'XEL', 'XLNX', 'ZM']
symbols_russel1000 = ['TWOU', 'MMM', 'ABT', 'ABBV', 'ABMD', 'ACHC', 'ACN', 'ATVI', 'AYI', 'ADNT', 'ADBE', 'ADT', 'AAP', 'AMD', 'ACM', 'AES', 'AMG', 'AFL', 'AGCO', 'A', 'AGIO', 'AGNC', 'AL', 'APD', 'AKAM', 'ALK', 'ALB', 'AA', 'ARE', 'ALXN', 'ALGN', 'ALKS', 'Y', 'ALLE', 'AGN', 'ADS', 'LNT', 'ALSN', 'ALL', 'ALLY', 'ALNY', 'GOOGL', 'GOOG', 'MO', 'AMZN', 'AMCX', 'DOX', 'UHAL', 'AEE', 'AAL', 'ACC', 'AEP', 'AXP', 'AFG', 'AMH', 'AIG', 'ANAT', 'AMT', 'AWK', 'AMP', 'ABC', 'AME', 'AMGN', 'APH', 'ADI', 'NLY', 'ANSS', 'AR', 'ANTM', 'AON', 'APA', 'AIV', 'APY', 'APLE', 'AAPL', 'AMAT', 'ATR', 'APTV', 'WTR', 'ARMK', 'ACGL', 'ADM', 'ARNC', 'ARD', 'ANET', 'AWI', 'ARW', 'ASH', 'AZPN', 'ASB', 'AIZ', 'AGO', 'T', 'ATH', 'TEAM', 'ATO', 'ADSK', 'ADP', 'AN', 'AZO', 'AVB', 'AGR', 'AVY', 'AVT', 'EQH', 'AXTA', 'AXS', 'BKR', 'BLL', 'BAC', 'BOH', 'BK', 'OZK', 'BKU', 'BAX', 'BDX', 'WRB', 'BRK.B', 'BERY', 'BBY', 'BYND', 'BGCP', 'BIIB', 'BMRN', 'BIO', 'TECH', 'BKI', 'BLK', 'HRB', 'BLUE', 'BA', 'BOKF', 'BKNG', 'BAH', 'BWA', 'BSX', 'BDN', 'BFAM', 'BHF', 'BMY', 'BRX', 'AVGO', 'BR', 'BPYU', 'BRO', 'BFA', 'BFB', 'BRKR', 'BC', 'BG', 'BURL', 'BWXT', 'CHRW', 'CABO', 'CBT', 'COG', 'CACI', 'CDNS', 'CZR', 'CPT', 'CPB', 'CMD', 'COF', 'CAH', 'CSL', 'KMX', 'CCL', 'CRI', 'CASY', 'CTLT', 'CAT', 'CBOE', 'CBRE', 'CBS', 'CDK', 'CDW', 'CE', 'CELG', 'CNC', 'CDEV', 'CNP', 'CTL', 'CDAY', 'BXP', 'CF', 'CRL', 'CHTR', 'CHE', 'LNG', 'CHK', 'CVX', 'CIM', 'CMG', 'CHH', 'CB', 'CHD', 'CI', 'XEC', 'CINF', 'CNK', 'CTAS', 'CSCO', 'CIT', 'C', 'CFG', 'CTXS', 'CLH', 'CLX', 'CME', 'CMS', 'CNA', 'CNX', 'KO', 'CGNX', 'CTSH', 'COHR', 'CFX', 'CL', 'CLNY', 'CXP', 'COLM', 'CMCSA', 'CMA', 'CBSH', 'COMM', 'CAG', 'CXO', 'CNDT', 'COP', 'ED', 'STZ', 'CERN', 'CPA', 'CPRT', 'CLGX', 'COR', 'GLW', 'OFC', 'CSGP', 'COST', 'COTY', 'CR', 'CACC', 'CCI', 'CCK', 'CSX', 'CUBE', 'CFR', 'CMI', 'CW', 'CVS', 'CY', 'CONE', 'DHI', 'DHR', 'DRI', 'DVA', 'SITC', 'DE', 'DELL', 'DAL', 'XRAY', 'DVN', 'DXCM', 'FANG', 'DKS', 'DLR', 'DFS', 'DISCA', 'DISCK', 'DISH', 'DIS', 'DHC', 'DOCU', 'DLB', 'DG', 'DLTR', 'D', 'DPZ', 'CLR', 'COO', 'DEI', 'DOV', 'DD', 'DPS', 'DTE', 'DUK', 'DRE', 'DNB', 'DNKN', 'DXC', 'ETFC', 'EXP', 'EWBC', 'EMN', 'ETN', 'EV', 'EBAY', 'SATS', 'ECL', 'EIX', 'EW', 'EA', 'EMR', 'ESRT', 'EHC', 'EGN', 'ENR', 'ETR', 'EVHC', 'EOG', 'EPAM', 'EPR', 'EQT', 'EFX', 'EQIX', 'EQC', 'ELS', 'EQR', 'ERIE', 'ESS', 'EL', 'EEFT', 'EVBG', 'EVR', 'RE', 'EVRG', 'ES', 'UFS', 'DCI', 'EXPE', 'EXPD', 'STAY', 'EXR', 'XOG', 'XOM', 'FFIV', 'FB', 'FDS', 'FICO', 'FAST', 'FRT', 'FDX', 'FIS', 'FITB', 'FEYE', 'FAF', 'FCNCA', 'FDC', 'FHB', 'FHN', 'FRC', 'FSLR', 'FE', 'FISV', 'FLT', 'FLIR', 'FND', 'FLO', 'FLS', 'FLR', 'FMC', 'FNB', 'FNF', 'FL', 'F', 'FTNT', 'FTV', 'FBHS', 'FOXA', 'FOX', 'BEN', 'FCX', 'AJG', 'GLPI', 'GPS', 'EXAS', 'EXEL', 'EXC', 'GTES', 'GLIBA', 'GD', 'GE', 'GIS', 'GM', 'GWR', 'G', 'GNTX', 'GPC', 'GILD', 'GPN', 'GL', 'GDDY', 'GS', 'GT', 'GRA', 'GGG', 'EAF', 'GHC', 'GWW', 'LOPE', 'GPK', 'GRUB', 'GWRE', 'HAIN', 'HAL', 'HBI', 'THG', 'HOG', 'HIG', 'HAS', 'HE', 'HCA', 'HDS', 'HTA', 'PEAK', 'HEI.A', 'HEI', 'HP', 'JKHY', 'HLF', 'HSY', 'HES', 'GDI', 'GRMN', 'IT', 'HGV', 'HLT', 'HFC', 'HOLX', 'HD', 'HON', 'HRL', 'HST', 'HHC', 'HPQ', 'HUBB', 'HPP', 'HUM', 'HBAN', 'HII', 'HUN', 'H', 'IAC', 'ICUI', 'IEX', 'IDXX', 'INFO', 'ITW', 'ILMN', 'INCY', 'IR', 'INGR', 'PODD', 'IART', 'INTC', 'IBKR', 'ICE', 'IGT', 'IP', 'IPG', 'IBM', 'IFF', 'INTU', 'ISRG', 'IVZ', 'INVH', 'IONS', 'IPGP', 'IQV', 'HPE', 'HXL', 'HIW', 'HRC', 'JAZZ', 'JBHT', 'JBGS', 'JEF', 'JBLU', 'JNJ', 'JCI', 'JLL', 'JPM', 'JNPR', 'KSU', 'KAR', 'K', 'KEY', 'KEYS', 'KRC', 'KMB', 'KIM', 'KMI', 'KEX', 'KLAC', 'KNX', 'KSS', 'KOS', 'KR', 'LB', 'LHX', 'LH', 'LRCX', 'LAMR', 'LW', 'LSTR', 'LVS', 'LAZ', 'LEA', 'LM', 'LEG', 'LDOS', 'LEN', 'LEN.B', 'LII', 'LBRDA', 'LBRDK', 'FWONA', 'IRM', 'ITT', 'JBL', 'JEC', 'LLY', 'LECO', 'LNC', 'LGF.A', 'LGF.B', 'LFUS', 'LYV', 'LKQ', 'LMT', 'L', 'LOGM', 'LOW', 'LPLA', 'LULU', 'LYFT', 'LYB', 'MTB', 'MAC', 'MIC', 'M', 'MSG', 'MANH', 'MAN', 'MRO', 'MPC', 'MKL', 'MKTX', 'MAR', 'MMC', 'MLM', 'MRVL', 'MAS', 'MASI', 'MA', 'MTCH', 'MAT', 'MXIM', 'MKC', 'MCD', 'MCK', 'MDU', 'MPW', 'MD', 'MDT', 'MRK', 'FWONK', 'LPT', 'LSXMA', 'LSXMK', 'LSI', 'CPRI', 'MIK', 'MCHP', 'MU', 'MSFT', 'MAA', 'MIDD', 'MKSI', 'MHK', 'MOH', 'TAP', 'MDLZ', 'MPWR', 'MNST', 'MCO', 'MS', 'MORN', 'MOS', 'MSI', 'MSM', 'MSCI', 'MUR', 'MYL', 'NBR', 'NDAQ', 'NFG', 'NATI', 'NOV', 'NNN', 'NAVI', 'NCR', 'NKTR', 'NTAP', 'NFLX', 'NBIX', 'NRZ', 'NYCB', 'NWL', 'NEU', 'NEM', 'NWSA', 'NWS', 'MCY', 'MET', 'MTD', 'MFA', 'MGM', 'JWN', 'NSC', 'NTRS', 'NOC', 'NLOK', 'NCLH', 'NRG', 'NUS', 'NUAN', 'NUE', 'NTNX', 'NVT', 'NVDA', 'NVR', 'NXPI', 'ORLY', 'OXY', 'OGE', 'OKTA', 'ODFL', 'ORI', 'OLN', 'OHI', 'OMC', 'ON', 'OMF', 'OKE', 'ORCL', 'OSK', 'OUT', 'OC', 'OI', 'PCAR', 'PKG', 'PACW', 'PANW', 'PGRE', 'PK', 'PH', 'PE', 'PTEN', 'PAYX', 'PAYC', 'PYPL', 'NEE', 'NLSN', 'NKE', 'NI', 'NBL', 'NDSN', 'PEP', 'PKI', 'PRGO', 'PFE', 'PCG', 'PM', 'PSX', 'PPC', 'PNFP', 'PF', 'PNW', 'PXD', 'ESI', 'PNC', 'PII', 'POOL', 'BPOP', 'POST', 'PPG', 'PPL', 'PRAH', 'PINC', 'TROW', 'PFG', 'PG', 'PGR', 'PLD', 'PFPT', 'PB', 'PRU', 'PTC', 'PSA', 'PEG', 'PHM', 'PSTG', 'PVH', 'QGEN', 'QRVO', 'QCOM', 'PWR', 'PBF', 'PEGA', 'PAG', 'PNR', 'PEN', 'PBCT', 'RLGY', 'RP', 'O', 'RBC', 'REG', 'REGN', 'RF', 'RGA', 'RS', 'RNR', 'RSG', 'RMD', 'RPAI', 'RNG', 'RHI', 'ROK', 'ROL', 'ROP', 'ROST', 'RCL', 'RGLD', 'RES', 'RPM', 'RSPP', 'R', 'SPGI', 'SABR', 'SAGE', 'CRM', 'SC', 'SRPT', 'SBAC', 'HSIC', 'SLB', 'SNDR', 'SCHW', 'SMG', 'SEB', 'SEE', 'DGX', 'QRTEA', 'RL', 'RRC', 'RJF', 'RYN', 'RTN', 'NOW', 'SVC', 'SHW', 'SBNY', 'SLGN', 'SPG', 'SIRI', 'SIX', 'SKX', 'SWKS', 'SLG', 'SLM', 'SM', 'AOS', 'SJM', 'SNA', 'SON', 'SO', 'SCCO', 'LUV', 'SPB', 'SPR', 'SRC', 'SPLK', 'S', 'SFM', 'SQ', 'SSNC', 'SWK', 'SBUX', 'STWD', 'STT', 'STLD', 'SRCL', 'STE', 'STL', 'STOR', 'SYK', 'SUI', 'STI', 'SIVB', 'SWCH', 'SGEN', 'SEIC', 'SRE', 'ST', 'SCI', 'SERV', 'TPR', 'TRGP', 'TGT', 'TCO', 'TCF', 'AMTD', 'TDY', 'TFX', 'TDS', 'TPX', 'TDC', 'TER', 'TEX', 'TSRO', 'TSLA', 'TCBI', 'TXN', 'TXT', 'TFSL', 'CC', 'KHC', 'WEN', 'TMO', 'THO', 'TIF', 'TKR', 'TJX', 'TOL', 'TTC', 'TSCO', 'TDG', 'RIG', 'TRU', 'TRV', 'THS', 'TPCO', 'TRMB', 'TRN', 'TRIP', 'SYF', 'SNPS', 'SNV', 'SYY', 'DATA', 'TTWO', 'TMUS', 'TFC', 'UBER', 'UGI', 'ULTA', 'ULTI', 'UMPQ', 'UAA', 'UA', 'UNP', 'UAL', 'UPS', 'URI', 'USM', 'X', 'UTX', 'UTHR', 'UNH', 'UNIT', 'UNVR', 'OLED', 'UHS', 'UNM', 'URBN', 'USB', 'USFD', 'VFC', 'MTN', 'VLO', 'VMI', 'VVV', 'VAR', 'VVC', 'VEEV', 'VTR', 'VER', 'VRSN', 'VRSK', 'VZ', 'VSM', 'VRTX', 'VIAC', 'TWLO', 'TWTR', 'TWO', 'TYL', 'TSN', 'USG', 'UI', 'UDR', 'VMC', 'WPC', 'WBC', 'WAB', 'WBA', 'WMT', 'WM', 'WAT', 'WSO', 'W', 'WFTLF', 'WBS', 'WEC', 'WRI', 'WBT', 'WCG', 'WFC', 'WELL', 'WCC', 'WST', 'WAL', 'WDC', 'WU', 'WLK', 'WRK', 'WEX', 'WY', 'WHR', 'WTM', 'WLL', 'JW.A', 'WMB', 'WSM', 'WLTW', 'WTFC', 'WDAY', 'WP', 'WPX', 'WYND', 'WH', 'VIAB', 'VICI', 'VIRT', 'V', 'VC', 'VST', 'VMW', 'VNO', 'VOYA', 'ZAYO', 'ZBRA', 'ZEN', 'ZG', 'Z', 'ZBH', 'ZION', 'ZTS', 'ZNGA', 'WYNN', 'XEL', 'XRX', 'XLNX', 'XPO', 'XYL', 'YUMC', 'YUM']


# ftp.nasdaqtrader.com/SymbolDirectory ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt
# ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt

symbols_tase = []  #symbols_tase       = ['ALD.TA', 'ABIL.TA', 'ACCL.TA', 'ADGR.TA', 'ADKA.TA', 'ARDM.TA', 'AFHL.TA', 'AFPR.TA', 'AFID.TA', 'AFRE.TA', 'AICS.TA', 'ARPT.TA', 'ALBA.TA', 'ALMD.TA', 'ALLT.TA', 'AMDA.L.TA', 'ALMA.TA', 'ALGS.TA', 'ALHE.TA', 'ALRPR.TA', 'ASPF.TA', 'AMAN.TA', 'AMRK.TA', 'AMOT.TA', 'ANLT.TA', 'ANGL.TA', 'APIO.M.TA', 'APLP.TA', 'ARD.TA', 'ARAD.TA', 'ARAN.TA', 'ARNA.TA', 'ARKO.TA', 'ARYT.TA', 'ASHO.TA', 'ASHG.TA', 'ASPR.TA', 'ASGR.TA', 'ATRY.TA', 'AUDC.TA', 'AUGN.TA', 'AURA.TA', 'SHVA.TA', 'AVER.TA', 'AVGL.TA', 'AVIA.TA', 'AVIV.TA', 'AVLN.TA', 'AVRT.TA', 'AYAL.TA', 'AZRM.TA', 'AZRG.TA', 'BCOM.TA', 'BYAR.TA', 'BBYL.TA', 'BRAN.TA', 'BVC.TA', 'BYSD.TA', 'ORL.TA', 'BSEN.TA', 'BEZQ.TA', 'BGI-M.TA', 'BIG.TA', 'BIOV.TA', 'BOLT.TA', 'BLRX.TA', 'PHGE.TA', 'BIRM.TA', 'BLSR.TA', 'BOTI.TA', 'BONS.TA', 'BCNV.TA', 'BWAY.TA', 'BRAM.TA', 'BRND.TA', 'BNRG.TA', 'BRIL.TA', 'BRMG.TA', 'CISY.TA', 'CAMT.TA', 'CANF.TA', 'CSURE.TA', 'CNMD.TA', 'CNZN.TA', 'CPTP.TA', 'CRSO.TA', 'CRMT.TA', 'CAST.TA', 'CEL.TA', 'CHAM.TA', 'CHR.TA', 'CMCT.TA', 'CMCTP.TA', 'CTPL5.TA', 'CTPL1.TA', 'CLBV.TA', 'CBI.TA', 'CLIS.TA', 'CFX.TA', 'CDEV.TA', 'CGEN.TA', 'CMDR.TA', 'DNA.TA', 'DANH.TA', 'DANE.TA', 'DCMA.TA', 'DLRL.TA', 'DLEA.TA', 'DEDR.L.TA', 'DLEKG.TA', 'DELT.TA', 'DIMRI.TA', 'DIFI.TA', 'DSCT.TA', 'DISI.TA', 'DRAL.TA', 'DORL.TA', 'DRSL.TA', 'DUNI.TA', 'EMCO.TA', 'EDRL.TA', 'ELAL.TA', 'EMITF.TA', 'EMTC.TA', 'ESLT.TA', 'ELCO.TA', 'ELDAV.TA', 'ELTR.TA', 'ECP.TA', 'ELCRE.TA', 'ELWS.TA', 'ELLO.TA', 'ELMR.TA', 'ELRN.TA', 'ELSPC.TA', 'EMDV.TA', 'ENDY.TA', 'ENOG.TA', 'ENRG.TA', 'ENLT.TA', 'ENLV.TA', 'EQTL.TA', 'EFNC.TA', 'EVGN.TA', 'EXPO.TA', 'FNTS.TA', 'FTAL.TA', 'FIBI.TA', 'FIBIH.TA', 'FGAS.TA', 'FBRT.TA', 'FRSX.TA', 'FORTY.TA', 'FOX.TA', 'FRSM.TA', 'FRDN.TA', 'GOSS.TA', 'GFC-L.TA', 'GPGB.TA', 'GADS.TA', 'GSFI.TA', 'GAON.TA', 'GAGR.TA', 'GZT.TA', 'GNRS.TA', 'GIBUI.TA', 'GILT.TA', 'GNGR.TA', 'GIVO.L.TA', 'GIX.TA', 'GLTC.TA', 'GLEX.L.TA', 'GKL.TA', 'GLRS.TA', 'GODM-M.TA', 'GLPL.TA', 'GOLD.TA', 'GOHO.TA', 'GOLF.TA', 'HDST.TA', 'HAP.TA', 'HGG.TA', 'HAIN.TA', 'HMAM.TA', 'MSBI.TA', 'HAMAT.TA', 'HAML.TA', 'HNMR.TA', 'HARL.TA', 'HLAN.TA', 'HRON.TA', 'HOD.TA', 'HLMS.TA', 'IBI.TA', 'IBITEC.F.TA', 'ICB.TA', 'ICCM.TA', 'ICL.TA', 'IDIN.TA', 'IES.TA', 'IFF.TA', 'ILDR.TA', 'ILX.TA', 'IMCO.TA', 'INBR.TA', 'INFR.TA', 'INRM.TA', 'INTL.TA', 'ININ.TA', 'INCR.TA', 'INTR.TA', 'IGLD-M.TA', 'ISCD.TA', 'ISCN.TA', 'ILCO.TA', 'ISOP.L.TA', 'ISHI.TA', 'ISRA.L.TA', 'ISRS.TA', 'ISRO.TA', 'ISTA.TA', 'ITMR.TA', 'JBNK.TA', 'KDST.TA', 'KAFR.TA', 'KMDA.TA', 'KRNV-L.TA', 'KARE.TA', 'KRDI.TA', 'KEN.TA', 'KRUR.TA', 'KTOV.TA', 'KLIL.TA', 'KMNK-M.TA', 'KNFM.TA', 'LHIS.TA', 'LAHAV.TA', 'ILDC.TA', 'LPHL.L.TA', 'LAPD.TA', 'LDER.TA', 'LSCO.TA', 'LUMI.TA', 'LEOF.TA', 'LEVI.TA', 'LVPR.TA', 'LBTL.TA', 'LCTX.TA', 'LPSN.TA', 'LODZ.TA', 'LUDN.TA', 'LUZN.TA', 'LZNR.TA', 'MGIC.TA', 'MLTM.TA', 'MMAN.TA', 'MSLA.TA', 'MTMY.TA', 'MTRX.TA', 'MAXO.TA', 'MTRN.TA', 'MEAT.TA', 'MDGS.TA', 'MDPR.TA', 'MDTR.TA', 'MDVI.TA', 'MGOR.TA', 'MEDN.TA', 'MTDS.TA', 'MLSR.TA', 'MNIN.TA', 'MNRT.TA', 'MMHD.TA', 'CMER.TA', 'MRHL.TA', 'MSKE.TA', 'MGRT.TA', 'MCRNT.TA', 'MGDL.TA', 'MIFT.TA', 'MNGN.TA', 'MNRV.TA', 'MLD.TA', 'MSHR.TA', 'MVNE.TA', 'MISH.TA', 'MZTF.TA', 'MBMX-M.TA', 'MDIN.L.TA', 'MRIN.TA', 'MYSZ.TA', 'MYDS.TA', 'NFTA.TA', 'NVPT.L.TA', 'NAWI.TA', 'NTGR.TA', 'NTO.TA', 'NTML.TA', 'NERZ-M.TA', 'NXTG.TA', 'NXTM.TA', 'NXGN-M.TA', 'NICE.TA', 'NISA.TA', 'NSTR.TA', 'NVMI.TA', 'NVLG.TA', 'ORTC.TA', 'ONE.TA', 'OPAL.TA', 'OPCE.TA', 'OPK.TA', 'OBAS.TA', 'ORAD.TA', 'ORMP.TA', 'ORBI.TA', 'ORIN.TA', 'ORA.TA', 'ORON.TA', 'OVRS.TA', 'PCBT.TA', 'PLTF.TA', 'PLRM.TA', 'PNAX.TA', 'PTNR.TA', 'PAYT.TA', 'PZOL.TA', 'PEN.TA', 'PFLT.TA', 'PERI.TA', 'PRGO.TA', 'PTCH.TA', 'PTX.TA', 'PMCN.TA', 'PHOE.TA', 'PLSN.TA', 'PLCR.TA', 'PPIL-M.TA', 'PLAZ-L.TA', 'PSTI.TA', 'POLI.TA', 'PIU.TA', 'POLY.TA', 'PWFL.TA', 'PRSK.TA', 'PRTC.TA', 'PTBL.TA', 'PLX.TA', 'QLTU.TA', 'QNCO.TA', 'RLCO.TA', 'RMN.TA', 'RMLI.TA', 'RANI.TA', 'RPAC.TA', 'RATI.L.TA', 'RTPT.L.TA', 'RAVD.TA', 'RVL.TA', 'RIT1.TA', 'AZRT.TA', 'REKA.TA', 'RIMO.TA', 'ROBO.TA', 'RTEN.L.TA', 'ROTS.TA', 'RSEL.TA', 'SRAC.TA', 'SFET.TA', 'SANO1.TA', 'SPNS.TA', 'SRFT.TA', 'STCM.TA', 'SAVR.TA', 'SHNP.TA', 'SCOP.TA', 'SEMG.TA', 'SLARL.TA', 'SHGR.TA', 'SALG.TA', 'SHAN.TA', 'SPEN.TA', 'SEFA.TA', 'SMNIN.TA', 'SKBN.TA', 'SHOM.TA', 'SAE.TA', 'SKLN.TA', 'SLGN.TA', 'SMTO.TA', 'SCC.TA', 'SPRG.TA', 'SPNTC.TA', 'STG.TA', 'STRS.TA', 'SMT.TA', 'SNFL.TA', 'SNCM.TA', 'SPGE.TA', 'SNEL.TA', 'TDGN-L.TA', 'TDRN.TA', 'TALD.TA', 'TMRP.TA', 'TASE.TA', 'TATT.TA', 'TAYA.TA', 'TNPV.TA', 'TEDE.TA', 'TFRLF.TA', 'TLRD.TA', 'TLSY.TA', 'TUZA.TA', 'TEVA.TA', 'TIGBUR.TA', 'TKUN.TA', 'TTAM.TA', 'TGTR.TA', 'TOPS.TA', 'TSEM.TA', 'TREN.TA', 'UNCR.TA', 'UNCT.L.TA', 'UNIT.TA', 'UNVO.TA', 'UTRN.TA', 'VCTR.TA', 'VILR.TA', 'VISN.TA', 'VTLC-M.TA', 'VTNA.TA', 'VNTZ-M.TA', 'WSMK.TA', 'WTS.TA', 'WILC.TA', 'WLFD.TA', 'XENA.TA', 'XTLB.TA', 'YAAC.TA', 'YBOX.TA', 'YHNF.TA', 'ZNKL.TA', 'ZMH.TA', 'ZUR.TA']
if TASE_MODE:
    tase_filenames_list = ['Indices/Data_20201023.csv']

    for filename in tase_filenames_list:
        with open(filename, mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0
            for row in reader:
                if row_index <= 3:
                    row_index += 1
                    continue
                else:
                    symbols_tase.append(row[1]+'.TA')
                    row_index += 1

    stocks_list_tase = investpy.get_stocks_list(country='israel')
    for index, stock in enumerate(stocks_list_tase): stocks_list_tase[index] += '.TA'

symbols_united_states     = []
stocks_list_united_states = []
if READ_UNITED_STATES_INPUT_SYMBOLS:
    nasdaq_filenames_list = ['Indices/nasdaqlisted.csv', 'Indices/otherlisted.csv']

    for filename in nasdaq_filenames_list:
        with open(filename, mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter='|')
            row_index = 0
            for row in reader:
                if row_index == 0 or 'ETF' in row[1]:
                    row_index += 1
                    continue
                else:
                    symbols_united_states.append(row[0])
                    row_index += 1

    stocks_list_united_states = investpy.get_stocks_list(country='united states')


symbols = symbols_snp500 + symbols_nasdaq100 + symbols_russel1000 + symbols_united_states + stocks_list_united_states

if TASE_MODE:
    symbols = symbols_tase + stocks_list_tase

symbols = list(set(symbols))


# Temporary for test:
# symbols = ['LEN.B', 'XOG', 'BKR', 'ALMA.TA', 'EMDV.TA', 'ISTA.TA', 'ALD.TA', 'ADGR.TA', 'HOLX', 'SKLN.TA', 'ALMA.TA', 'BR', 'GDI', 'LOGM', 'WRK', 'EBAY', 'RSPP', 'FB', 'AL', 'INTC', 'AES', 'MMM', 'ADBE', 'MS']

print('\nSSS Symbols to Scan: {}\n'.format(symbols))


def check_quote_type(stock_data):
    if stock_data.quote_type == MUTUALFUND:
        print('Mutual Fund: Skip')
        return False  # Not interested in those and they lack all the below info[] properties so nothing to do with them anyways
    return True


def check_sector(stock_data):
    if len(SECTORS_LIST) and stock_data.sector not in SECTORS_LIST:
        print('              Skipping Sector {}'.format(stock_data.sector))
        return False
    return True


def text_to_num(text):
    d = {
        'K': 1000,
        'M': 1000000,
        'B': 1000000000,
        'T': 1000000000000
    }
    if not isinstance(text, str):
        # Non-strings are bad are missing data in poster's submission
        return 0

    text = text.replace(' ','')

    if text[-1] in d:  # separate out the K, M, B or T
        num, magnitude = text[:-1], text[-1]
        return int(float(num) * d[magnitude])
    else:
        return float(text)


def process_info(symbol, stock_data):
    try:
        return_value = True
        info              = {}
        stock_information = {}
        if BUILD_CSV_DB:
            try:
                info = symbol.get_info()
            except Exception as e:
                print("              Exception in {} symbol.get_info(): {}".format(stock_data.ticker, e))
                pass

            try:
                if TASE_MODE:
                    stock_information = investpy.get_stock_information(stock=stock_data.ticker.replace('.TA',''), country='israel', as_json=True)
                else:
                    stock_information = investpy.get_stock_information(stock=stock_data.ticker, country='united states', as_json=True)
            except Exception as e:
                print("              Exception in {} get_stock_information(): {}".format(stock_data.ticker, e))
                pass

        if BUILD_CSV_DB:
            if 'shortName' in info: stock_data.short_name = info['shortName']
            else:                   stock_data.short_name = 'None'

        if stock_data.short_name is not None: print('{:35} - '.format(stock_data.short_name), end='')

        if BUILD_CSV_DB and 'quoteType' in info: stock_data.quote_type = info['quoteType']
        if not check_quote_type(stock_data):     return False

        if BUILD_CSV_DB and 'sector' in info:    stock_data.sector = info['sector']
        if not check_sector(stock_data):         return_value = False

        if BUILD_CSV_DB:
            if 'fullTimeEmployees' in info:      stock_data.num_employees = info['fullTimeEmployees']
            else:                                stock_data.num_employees = NUM_EMPLOYEES_UNKNOWN
            if stock_data.num_employees is None: stock_data.num_employees = NUM_EMPLOYEES_UNKNOWN

            # Special exception for Intel (INTC) - Bug in Yahoo Finance:
            if stock_data.ticker == 'INTC' and stock_data.num_employees < 1000:
                stock_data.num_employees *= 1000

        if BUILD_CSV_DB:
            if 'profitMargins' in info:          stock_data.profit_margin = info['profitMargins']
            else:                                stock_data.profit_margin = PROFIT_MARGIN_UNKNOWN
            if stock_data.profit_margin is None: stock_data.profit_margin = PROFIT_MARGIN_UNKNOWN

            if 'heldPercentInstitutions' in info:                                                         stock_data.held_percent_institutions = info['heldPercentInstitutions']
            else:                                                                                         stock_data.held_percent_institutions = PERCENT_HELD_INSTITUTIONS_LOW
            if stock_data.held_percent_institutions is None or stock_data.held_percent_institutions == 0: stock_data.held_percent_institutions = PERCENT_HELD_INSTITUTIONS_LOW

            if 'enterpriseToRevenue' in info:                          stock_data.enterprise_value_to_revenue = info['enterpriseToRevenue']  # https://www.investopedia.com/terms/e/ev-revenue-multiple.asp
            else:                                                      stock_data.enterprise_value_to_revenue = None
            if isinstance(stock_data.enterprise_value_to_revenue,str): stock_data.enterprise_value_to_revenue = None

            if 'enterpriseToEbitda' in info:                           stock_data.enterprise_value_to_ebitda  = info['enterpriseToEbitda']  # The lower the better: https://www.investopedia.com/ask/answers/072715/what-considered-healthy-evebitda.asp
            else:                                                      stock_data.enterprise_value_to_ebitda  = None
            if isinstance(stock_data.enterprise_value_to_ebitda,str):  stock_data.enterprise_value_to_ebitda  = None

            if 'trailingPE' in info:                                   stock_data.trailing_price_to_earnings  = info['trailingPE']  # https://www.investopedia.com/terms/t/trailingpe.asp
            else:                                                      stock_data.trailing_price_to_earnings  = None
            if isinstance(stock_data.trailing_price_to_earnings,str):  stock_data.trailing_price_to_earnings  = None

        if stock_data.enterprise_value_to_revenue is None and stock_data.enterprise_value_to_ebitda is None and stock_data.trailing_price_to_earnings is None:
            if 'P/E Ratio' in stock_information and stock_information['P/E Ratio'] is not None:
                stock_data.trailing_price_to_earnings = float(text_to_num(stock_information['P/E Ratio']))
            else:
                if return_value: print('              Skipping since trailing_price_to_earnings, enterprise_value_to_ebitda and enterprise_value_to_revenue are unknown')
                return_value = False

        if BUILD_CSV_DB:
            if   stock_data.enterprise_value_to_revenue is None and stock_data.enterprise_value_to_ebitda  is not None: stock_data.enterprise_value_to_revenue = stock_data.enterprise_value_to_ebitda
            elif stock_data.enterprise_value_to_revenue is None and stock_data.trailing_price_to_earnings  is not None: stock_data.enterprise_value_to_revenue = stock_data.trailing_price_to_earnings

            if   stock_data.enterprise_value_to_ebitda  is None and stock_data.enterprise_value_to_revenue is not None: stock_data.enterprise_value_to_ebitda  = stock_data.enterprise_value_to_revenue
            elif stock_data.enterprise_value_to_ebitda  is None and stock_data.trailing_price_to_earnings  is not None: stock_data.enterprise_value_to_ebitda  = stock_data.trailing_price_to_earnings

            if   stock_data.trailing_price_to_earnings  is None and stock_data.enterprise_value_to_revenue is not None: stock_data.trailing_price_to_earnings  = stock_data.enterprise_value_to_revenue
            elif stock_data.trailing_price_to_earnings  is None and stock_data.enterprise_value_to_ebitda  is not None: stock_data.trailing_price_to_earnings  = stock_data.enterprise_value_to_ebitda

            if 'forwardEps'                                 in info: stock_data.forward_eps                       = info['forwardEps']
            else:                                                    stock_data.forward_eps                       = None
            if isinstance(stock_data.forward_eps,str):               stock_data.forward_eps                       = None

            if 'trailingEps'                                in info: stock_data.trailing_eps                      = info['trailingEps']
            else:                                                    stock_data.trailing_eps                      = None
            if isinstance(stock_data.trailing_eps,str):              stock_data.trailing_eps                      = None

            if 'priceToBook'                                in info: stock_data.price_to_book                     = info['priceToBook']
            else:                                                    stock_data.price_to_book                     = None
            if isinstance(stock_data.price_to_book,str):             stock_data.price_to_book                     = None

            if 'earningsQuarterlyGrowth'                    in info: stock_data.earnings_quarterly_growth         = info['earningsQuarterlyGrowth']
            else:                                                    stock_data.earnings_quarterly_growth         = None
            if stock_data.earnings_quarterly_growth         is None: stock_data.earnings_quarterly_growth         = EARNINGS_QUARTERLY_GROWTH_MIN

            if 'pegRatio'                                   in info: stock_data.price_to_earnings_to_growth_ratio = info['pegRatio']
            else:                                                    stock_data.price_to_earnings_to_growth_ratio = PEG_UNKNOWN
            if stock_data.price_to_earnings_to_growth_ratio is None: stock_data.price_to_earnings_to_growth_ratio = PEG_UNKNOWN

            if 'sharesOutstanding'                          in info: stock_data.shares_outstanding                = info['sharesOutstanding']
            else:                                                    stock_data.shares_outstanding                = SHARES_OUTSTANDING_UNKNOWN
            if stock_data.shares_outstanding is None or stock_data.shares_outstanding == 0:
                if 'Shares Outstanding' in stock_information and stock_information['Shares Outstanding'] is not None:
                    stock_data.shares_outstanding = int(text_to_num(stock_information['Shares Outstanding']))
                else:
                    stock_data.shares_outstanding = SHARES_OUTSTANDING_UNKNOWN

            if 'netIncomeToCommon' in info: stock_data.net_income_to_common_shareholders = info['netIncomeToCommon']
            else:                           stock_data.net_income_to_common_shareholders = None

        if BUILD_CSV_DB:
            if 'enterpriseValue' in info and info['enterpriseValue'] is not None: stock_data.enterprise_value = info['enterpriseValue']


            if MARKET_CAP_INCLUDED:
                if stock_data.enterprise_value is None or stock_data.enterprise_value == 0:
                    if   'marketCap' in info and info['marketCap'] is not None:
                        stock_data.enterprise_value = int(info['marketCap'])
                    elif 'MarketCap' in stock_information and stock_information['MarketCap'] is not None:
                        stock_data.enterprise_value = int(text_to_num(stock_information['MarketCap']))

        if not TASE_MODE and (stock_data.enterprise_value is None or stock_data.enterprise_value < MIN_ENTERPRISE_VALUE):
            if return_value: print('              Skipping enterprise_value: {}'.format(stock_data.enterprise_value))
            return_value = False

        if stock_data.enterprise_value_to_revenue is None and stock_data.enterprise_value is not None and 'Revenue' in stock_information and stock_information['Revenue'] is not None  and text_to_num(stock_information['Revenue']) > 0:
            stock_data.enterprise_value_to_revenue = float(stock_data.enterprise_value)/float(text_to_num(stock_information['Revenue']))

        if stock_data.enterprise_value_to_revenue is None or stock_data.enterprise_value_to_revenue <= 0 or stock_data.enterprise_value_to_revenue > ENTERPRISE_VALUE_TO_REVENUE_LIMIT:
            if return_value: print('              Skipping enterprise_value_to_revenue: {}'.format(stock_data.enterprise_value_to_revenue))
            return_value = False

        if stock_data.enterprise_value_to_ebitda is None or stock_data.enterprise_value_to_ebitda <= 0:
            if return_value: print('              Skipping enterprise_value_to_ebitda: {}'.format(stock_data.enterprise_value_to_ebitda))
            return_value = False

        if stock_data.trailing_price_to_earnings is None or stock_data.trailing_price_to_earnings <= 0:
            if return_value: print('              Skipping trailing_price_to_earnings: {}'.format(stock_data.trailing_price_to_earnings))
            return_value = False

        if stock_data.profit_margin is None or stock_data.profit_margin < PROFIT_MARGIN_LIMIT or stock_data.profit_margin <= 0:
            if stock_data.profit_margin is not None and (not TASE_MODE or stock_data.profit_margin <= 0):
                if return_value: print('              Skipping profit_margin: {}'.format(stock_data.profit_margin))
                return_value = False

        if stock_data.trailing_eps is None:
            if 'EPS' in stock_information and stock_information['EPS'] is not None:
                stock_data.trailing_eps = float(text_to_num(stock_information['EPS']))

        if stock_data.trailing_eps is None or stock_data.trailing_eps is not None and stock_data.trailing_eps <= 0:
            if return_value: print('              Skipping trailing_eps: {}'.format(stock_data.trailing_eps))
            return_value = False

        if FORWARD_EPS_INCLUDED and (stock_data.forward_eps is None or stock_data.forward_eps is not None and stock_data.forward_eps <= 0):
            if return_value: print('              Skipping forward_eps: {}'.format(stock_data.forward_eps))
            return_value = False

        if stock_data.earnings_quarterly_growth is None or stock_data.earnings_quarterly_growth < EARNINGS_QUARTERLY_GROWTH_MIN:
            if return_value: print('              Skipping earnings_quarterly_growth: {}'.format(stock_data.earnings_quarterly_growth))
            return_value = False

        if stock_data.price_to_earnings_to_growth_ratio is None or stock_data.price_to_earnings_to_growth_ratio < 0:
            if return_value: print('              Skipping price_to_earnings_to_growth_ratio: {}'.format(stock_data.price_to_earnings_to_growth_ratio))
            if return_value: return_value = False

        if stock_data.net_income_to_common_shareholders is None or stock_data.net_income_to_common_shareholders < 0:
            if return_value: print('              Skipping net_income_to_common_shareholders: {}'.format(stock_data.net_income_to_common_shareholders))
            if return_value: return_value = False


        if return_value:
            stock_data.nitcsh_to_shares_outstanding = float(stock_data.net_income_to_common_shareholders) / float(stock_data.shares_outstanding)
            stock_data.nitcsh_to_num_employees      = float(stock_data.net_income_to_common_shareholders) / float(stock_data.num_employees)

            stock_data.sss_value     = stock_data.enterprise_value_to_revenue
            stock_data.ssss_value    = stock_data.price_to_earnings_to_growth_ratio
            stock_data.sssss_value   = stock_data.trailing_price_to_earnings
            stock_data.ssse_value    = stock_data.profit_margin
            stock_data.sssse_value   = stock_data.nitcsh_to_num_employees
            stock_data.ssssse_value  = stock_data.nitcsh_to_num_employees

            stock_data.sssi_value    = stock_data.enterprise_value_to_revenue
            stock_data.ssssi_value   = stock_data.price_to_earnings_to_growth_ratio
            stock_data.sssssi_value  = stock_data.trailing_price_to_earnings
            stock_data.sssei_value   = stock_data.profit_margin
            stock_data.ssssei_value  = stock_data.nitcsh_to_num_employees
            stock_data.sssssei_value = stock_data.nitcsh_to_num_employees

            # Rounding to non-None values + set None values to 0 for simplicity:
            if stock_data.sss_value                         is not None: stock_data.sss_value                         = round(stock_data.sss_value,                         NUM_ROUND_DECIMALS)
            if stock_data.ssss_value                        is not None: stock_data.ssss_value                        = round(stock_data.ssss_value,                        NUM_ROUND_DECIMALS)
            if stock_data.sssss_value                       is not None: stock_data.sssss_value                       = round(stock_data.sssss_value,                       NUM_ROUND_DECIMALS)
            if stock_data.ssse_value                        is not None: stock_data.ssse_value                        = round(stock_data.ssse_value,                        NUM_ROUND_DECIMALS)
            if stock_data.sssse_value                       is not None: stock_data.sssse_value                       = round(stock_data.sssse_value,                       NUM_ROUND_DECIMALS)
            if stock_data.ssssse_value                      is not None: stock_data.ssssse_value                      = round(stock_data.ssssse_value,                      NUM_ROUND_DECIMALS)
            if stock_data.sssi_value                        is not None: stock_data.sssi_value                        = round(stock_data.sssi_value,                        NUM_ROUND_DECIMALS)
            if stock_data.ssssi_value                       is not None: stock_data.ssssi_value                       = round(stock_data.ssssi_value,                       NUM_ROUND_DECIMALS)
            if stock_data.sssssi_value                      is not None: stock_data.sssssi_value                      = round(stock_data.sssssi_value,                      NUM_ROUND_DECIMALS)
            if stock_data.sssei_value                       is not None: stock_data.sssei_value                       = round(stock_data.sssei_value,                       NUM_ROUND_DECIMALS)
            if stock_data.ssssei_value                      is not None: stock_data.ssssei_value                      = round(stock_data.ssssei_value,                      NUM_ROUND_DECIMALS)
            if stock_data.sssssei_value                     is not None: stock_data.sssssei_value                     = round(stock_data.sssssei_value,                     NUM_ROUND_DECIMALS)
            if stock_data.enterprise_value_to_revenue       is not None: stock_data.enterprise_value_to_revenue       = round(stock_data.enterprise_value_to_revenue,       NUM_ROUND_DECIMALS)
            if stock_data.trailing_price_to_earnings        is not None: stock_data.trailing_price_to_earnings        = round(stock_data.trailing_price_to_earnings,        NUM_ROUND_DECIMALS)
            if stock_data.enterprise_value_to_ebitda        is not None: stock_data.enterprise_value_to_ebitda        = round(stock_data.enterprise_value_to_ebitda,        NUM_ROUND_DECIMALS)
            if stock_data.profit_margin                     is not None: stock_data.profit_margin                     = round(stock_data.profit_margin,                     NUM_ROUND_DECIMALS)
            if stock_data.held_percent_institutions         is not None: stock_data.held_percent_institutions         = round(stock_data.held_percent_institutions,         NUM_ROUND_DECIMALS)
            if stock_data.forward_eps                       is not None: stock_data.forward_eps                       = round(stock_data.forward_eps,                       NUM_ROUND_DECIMALS)
            if stock_data.trailing_eps                      is not None: stock_data.trailing_eps                      = round(stock_data.trailing_eps,                      NUM_ROUND_DECIMALS)
            if stock_data.price_to_book                     is not None: stock_data.price_to_book                     = round(stock_data.price_to_book,                     NUM_ROUND_DECIMALS)
            if stock_data.shares_outstanding                is not None: stock_data.shares_outstanding                = round(stock_data.shares_outstanding,                NUM_ROUND_DECIMALS)
            if stock_data.net_income_to_common_shareholders is not None: stock_data.net_income_to_common_shareholders = round(stock_data.net_income_to_common_shareholders, NUM_ROUND_DECIMALS)
            if stock_data.nitcsh_to_shares_outstanding      is not None: stock_data.nitcsh_to_shares_outstanding      = round(stock_data.nitcsh_to_shares_outstanding,      NUM_ROUND_DECIMALS)
            if stock_data.num_employees                     is not None: stock_data.num_employees                     = round(stock_data.num_employees,                     NUM_ROUND_DECIMALS)
            if stock_data.nitcsh_to_num_employees           is not None: stock_data.nitcsh_to_num_employees           = round(stock_data.nitcsh_to_num_employees,           NUM_ROUND_DECIMALS)
            if stock_data.earnings_quarterly_growth         is not None: stock_data.earnings_quarterly_growth         = round(stock_data.earnings_quarterly_growth,         NUM_ROUND_DECIMALS)
            if stock_data.price_to_earnings_to_growth_ratio is not None: stock_data.price_to_earnings_to_growth_ratio = round(stock_data.price_to_earnings_to_growth_ratio, NUM_ROUND_DECIMALS)
        else:
            stock_data.sss_value     = BAD_SSSE
            stock_data.ssss_value    = BAD_SSSE
            stock_data.sssss_value   = BAD_SSSE
            stock_data.ssse_value    = BAD_SSSE
            stock_data.sssse_value   = BAD_SSSE
            stock_data.ssssse_value  = BAD_SSSE
            stock_data.sssi_value    = BAD_SSS
            stock_data.ssssi_value   = BAD_SSS
            stock_data.sssssi_value  = BAD_SSS
            stock_data.sssei_value   = BAD_SSS
            stock_data.ssssei_value  = BAD_SSS
            stock_data.sssssei_value = BAD_SSS


        if BUILD_CSV_DB:
            if stock_data.sss_value                         is     None: stock_data.sss_value                         = BAD_SSS
            if stock_data.ssss_value                        is     None: stock_data.ssss_value                        = BAD_SSS
            if stock_data.sssss_value                       is     None: stock_data.sssss_value                       = BAD_SSS
            if stock_data.ssse_value                        is     None: stock_data.ssse_value                        = BAD_SSSE
            if stock_data.sssse_value                       is     None: stock_data.sssse_value                       = BAD_SSSE
            if stock_data.ssssse_value                      is     None: stock_data.ssssse_value                      = BAD_SSSE
            if stock_data.sssi_value                        is     None: stock_data.sssi_value                        = BAD_SSS
            if stock_data.ssssi_value                       is     None: stock_data.ssssi_value                       = BAD_SSS
            if stock_data.sssssi_value                      is     None: stock_data.sssssi_value                      = BAD_SSS
            if stock_data.sssei_value                       is     None: stock_data.sssei_value                       = BAD_SSSE
            if stock_data.ssssei_value                      is     None: stock_data.ssssei_value                      = BAD_SSSE
            if stock_data.sssssei_value                     is     None: stock_data.sssssei_value                     = BAD_SSSE
            if stock_data.enterprise_value_to_revenue       is     None: stock_data.enterprise_value_to_revenue       = 0
            if stock_data.trailing_price_to_earnings        is     None: stock_data.trailing_price_to_earnings        = 0
            if stock_data.enterprise_value_to_ebitda        is     None: stock_data.enterprise_value_to_ebitda        = 0
            if stock_data.profit_margin                     is     None: stock_data.profit_margin                     = 0
            if stock_data.held_percent_institutions         is     None: stock_data.held_percent_institutions         = 0
            if stock_data.forward_eps                       is     None: stock_data.forward_eps                       = 0
            if stock_data.trailing_eps                      is     None: stock_data.trailing_eps                      = 0
            if stock_data.price_to_book                     is     None: stock_data.price_to_book                     = 0
            if stock_data.shares_outstanding                is     None: stock_data.shares_outstanding                = 0
            if stock_data.net_income_to_common_shareholders is     None: stock_data.net_income_to_common_shareholders = 0
            if stock_data.nitcsh_to_shares_outstanding      is     None: stock_data.nitcsh_to_shares_outstanding      = 0
            if stock_data.num_employees                     is     None: stock_data.num_employees                     = 0
            if stock_data.nitcsh_to_num_employees           is     None: stock_data.nitcsh_to_num_employees           = 0
            if stock_data.earnings_quarterly_growth         is     None: stock_data.earnings_quarterly_growth         = 0
            if stock_data.price_to_earnings_to_growth_ratio is     None: stock_data.price_to_earnings_to_growth_ratio = 0

            stock_data.last_4_dividends_0 = 0
            stock_data.last_4_dividends_1 = 0
            stock_data.last_4_dividends_2 = 0
            stock_data.last_4_dividends_3 = 0

            # try: TODO: ASAFR: Complete this backup data to the yfinance dividends information
            #     if TASE_MODE:
            #         stock_dividends = investpy.get_stock_dividends(stock=stock_data.ticker.replace('.TA',''), country='israel')
            #     else:
            #         stock_dividends = investpy.get_stock_dividends(stock=stock_data.ticker, country='united states')
            #     # print("stock_dividends: {}".format(stock_dividends.values.tolist()))
            # except Exception as e:
            #     print("Exception in investpy symbol.dividends: {}".format(e))
            #     pass

            try:
                if len(symbol.dividends) > 0: stock_data.last_4_dividends_0 = symbol.dividends[0]
                if len(symbol.dividends) > 1: stock_data.last_4_dividends_1 = symbol.dividends[1]
                if len(symbol.dividends) > 2: stock_data.last_4_dividends_2 = symbol.dividends[2]
                if len(symbol.dividends) > 3:
                    stock_data.last_4_dividends_3 = symbol.dividends[3]
                    # print("symbol.dividends[0..3]: {},{},{},{}".format(symbol.dividends[0], symbol.dividends[1], symbol.dividends[2], symbol.dividends[3]))

            except Exception as e:
                print("Exception in symbol.dividends: {}".format(e))
                pass

        if return_value: print('              sector: {:15}, sss_value: {:15}, ssss_value: {:15}, sssss_value: {:15}, ssse_value: {:15}, sssse_value: {:15}, ssssse_value: {:15}, sssi_value: {:15}, ssssi_value: {:15}, sssssi_value: {:15}, sssei_value: {:15}, ssssei_value: {:15}, sssssei_value: {:15}, enterprise_value_to_revenue: {:15}, trailing_price_to_earnings: {:15}, enterprise_value_to_ebitda: {:15}, profit_margin: {:15}, held_percent_institutions: {:15}, forward_eps: {:15}, trailing_eps: {:15}, price_to_book: {:15}, shares_outstanding: {:15}, net_income_to_common_shareholders: {:15}, nitcsh_to_shares_outstanding: {:15}, num_employees: {:15}, enterprise_value: {:15}, nitcsh_to_num_employees: {:15}, earnings_quarterly_growth: {:15}, price_to_earnings_to_growth_ratio: {:15}'.format(stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.sssssei_value, stock_data.enterprise_value_to_revenue, stock_data.trailing_price_to_earnings, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio))
        return return_value

    except Exception as e:  # More information is output when exception is used instead of Exception
        print("              Exception in {} info: {}".format(stock_data.ticker, e))
        return False


def process_symbols(symbols, csv_db_data, rows, rows_no_div, rows_only_div, thread_id):
    iteration = 0
    if BUILD_CSV_DB:
        for symb in symbols:
            iteration += 1
            print('[Building DB: thread_id {}] Checking {:9} ({:4}/{:4}/{:4}): '.format(thread_id, symb, len(rows), iteration, len(symbols)), end='')
            symbol = yf.Ticker(symb)
            stock_data = StockData(ticker=symb)
            if not process_info(symbol=symbol, stock_data=stock_data):
                if TASE_MODE and 'TLV:' not in stock_data.ticker: stock_data.ticker = 'TLV:' + stock_data.ticker.replace('.TA', '')
                csv_db_data.append([stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.ssssei_value, stock_data.enterprise_value_to_revenue, stock_data.trailing_price_to_earnings, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
                continue

            if TASE_MODE and 'TLV:' not in stock_data.ticker: stock_data.ticker = 'TLV:' + stock_data.ticker.replace('.TA', '')
            dividends_sum = stock_data.last_4_dividends_0+stock_data.last_4_dividends_1+stock_data.last_4_dividends_2+stock_data.last_4_dividends_3
            rows.append(                           [stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.ssssei_value, stock_data.enterprise_value_to_revenue, stock_data.trailing_price_to_earnings, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
            if dividends_sum: rows_only_div.append([stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.ssssei_value, stock_data.enterprise_value_to_revenue, stock_data.trailing_price_to_earnings, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
            else:             rows_no_div.append(  [stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.ssssei_value, stock_data.enterprise_value_to_revenue, stock_data.trailing_price_to_earnings, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
            csv_db_data.append(                    [stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.ssssei_value, stock_data.enterprise_value_to_revenue, stock_data.trailing_price_to_earnings, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
    else: # DB already present
        for row in csv_db_data:
            iteration += 1
            symbol = row[0]
            print('[Existing DB: thread_id {}] Checking {:9} ({:4}/{:4}/{:4}): '.format(thread_id, symbol, len(rows), iteration, len(symbols)), end='')
            symbol = row[0]

            for fix_row_index in range(3,len(row)):  # for empty strings - convert value to 0
                if row[fix_row_index] == '': row[fix_row_index] = 0
            stock_data = StockData(ticker=symbol, short_name=row[1], sector=row[2], sss_value=float(row[3]), ssss_value=float(row[4]), sssss_value=float(row[5]), ssse_value=float(row[6]), sssse_value=float(row[7]), ssssse_value=float(row[8]), sssi_value=float(row[9]), ssssi_value=float(row[10]), sssssi_value=float(row[11]), sssei_value=float(row[12]), ssssei_value=float(row[13]), sssssei_value=float(row[14]), enterprise_value_to_revenue=float(row[15]), trailing_price_to_earnings=float(row[16]), enterprise_value_to_ebitda=float(row[17]), profit_margin=float(row[18]), held_percent_institutions=float(row[19]), forward_eps=float(row[20]), trailing_eps=float(row[21]), price_to_book=float(row[22]), shares_outstanding=float(row[23]), net_income_to_common_shareholders=float(row[24]), nitcsh_to_shares_outstanding=float(row[25]), num_employees=int(row[26]), enterprise_value=int(row[27]), nitcsh_to_num_employees=float(row[28]), earnings_quarterly_growth=float(row[29]), price_to_earnings_to_growth_ratio=float(row[30]), last_4_dividends_0=float(row[31]), last_4_dividends_1=float(row[32]), last_4_dividends_2=float(row[33]), last_4_dividends_3=float(row[34]))
            if not process_info(symbol=symbol, stock_data=stock_data):
                continue

            if TASE_MODE: stock_data.ticker = 'TLV:' + stock_data.ticker.replace('.TA', '')

            dividends_sum = stock_data.last_4_dividends_0 + stock_data.last_4_dividends_1 + stock_data.last_4_dividends_2 + stock_data.last_4_dividends_3
            rows.append([stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.ssssei_value, stock_data.enterprise_value_to_revenue, stock_data.trailing_price_to_earnings, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
            if dividends_sum:
                rows_only_div.append([stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.ssssei_value, stock_data.enterprise_value_to_revenue, stock_data.trailing_price_to_earnings, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
            else:
                rows_no_div.append([stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.ssssei_value, stock_data.enterprise_value_to_revenue, stock_data.trailing_price_to_earnings, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])


csv_db_data    = []
rows           = []
rows_no_div    = []
rows_only_div  = []
csv_db_data0   = []
rows0          = []
rows0_no_div   = []
rows0_only_div = []
csv_db_data1   = []
rows1          = []
rows1_no_div   = []
rows1_only_div = []
csv_db_data2   = []
rows2          = []
rows2_no_div   = []
rows2_only_div = []
csv_db_data3   = []
rows3          = []
rows3_no_div   = []
rows3_only_div = []
csv_db_data4   = []
rows4          = []
rows4_no_div   = []
rows4_only_div = []

if BUILD_CSV_DB == 0: # if DB is already present, read from it and prepare input to threads
    csv_db_filename = CSV_DB_PATH+'/db.csv'
    with open(csv_db_filename, mode='r', newline='') as engine:
        reader = csv.reader(engine, delimiter=',')
        row_index = 0
        for row in reader:
            if row_index == 0:
                row_index += 1
                continue
            else:
                if   (row_index-1) % NUM_THREADS == 0:
                    csv_db_data0.append(row)
                elif (row_index-1) % NUM_THREADS == 1:
                    csv_db_data1.append(row)
                elif (row_index-1) % NUM_THREADS == 2:
                    csv_db_data2.append(row)
                elif (row_index-1) % NUM_THREADS == 3:
                    csv_db_data3.append(row)
                elif (row_index-1) % NUM_THREADS == 4:
                    csv_db_data4.append(row)
                row_index += 1

if NUM_THREADS >= 1: symbols0 = symbols[0:][::NUM_THREADS] # 0,   NUM_THREADS,   2*NUM_THREADS,   3*NUM_THREADS, ...
if NUM_THREADS >= 2: symbols1 = symbols[1:][::NUM_THREADS] # 1, 1+NUM_THREADS, 2+2*NUM_THREADS, 2+3*NUM_THREADS, ...
if NUM_THREADS >= 3: symbols2 = symbols[2:][::NUM_THREADS] # 2, 2+NUM_THREADS, 3+2*NUM_THREADS, 3+3*NUM_THREADS, ...
if NUM_THREADS >= 4: symbols3 = symbols[3:][::NUM_THREADS] # 3, 3+NUM_THREADS, 4+2*NUM_THREADS, 4+3*NUM_THREADS, ...
if NUM_THREADS >= 5: symbols4 = symbols[4:][::NUM_THREADS] # 4, 4+NUM_THREADS, 5+2*NUM_THREADS, 5+3*NUM_THREADS, ...

if NUM_THREADS >= 1: thread0 = Thread(target=process_symbols, args=(symbols0, csv_db_data0, rows0, rows0_no_div, rows0_only_div, 0)) # process_symbols(symbols=symbols0, rows=rows0, rows_no_div=rows0_no_div, rows_only_div=rows0_only_div)
if NUM_THREADS >= 2: thread1 = Thread(target=process_symbols, args=(symbols1, csv_db_data1, rows1, rows1_no_div, rows1_only_div, 1)) # process_symbols(symbols=symbols1, rows=rows1, rows_no_div=rows1_no_div, rows_only_div=rows1_only_div)
if NUM_THREADS >= 3: thread2 = Thread(target=process_symbols, args=(symbols2, csv_db_data2, rows2, rows2_no_div, rows2_only_div, 2))
if NUM_THREADS >= 4: thread3 = Thread(target=process_symbols, args=(symbols3, csv_db_data3, rows3, rows3_no_div, rows3_only_div, 3))
if NUM_THREADS >= 5: thread4 = Thread(target=process_symbols, args=(symbols4, csv_db_data4, rows4, rows4_no_div, rows4_only_div, 4))

if NUM_THREADS >= 1: thread0.start()
if NUM_THREADS >= 2: thread1.start()
if NUM_THREADS >= 3: thread2.start()
if NUM_THREADS >= 4: thread3.start()
if NUM_THREADS >= 5: thread4.start()

if NUM_THREADS >= 1: thread0.join()
if NUM_THREADS >= 2: thread1.join()
if NUM_THREADS >= 3: thread2.join()
if NUM_THREADS >= 4: thread3.join()
if NUM_THREADS >= 5: thread4.join()

csv_db_data.extend(  csv_db_data0   + csv_db_data1   + csv_db_data2   + csv_db_data3   + csv_db_data4)
rows.extend(         rows0          + rows1          + rows2          + rows3          + rows4         )
rows_no_div.extend(  rows0_no_div   + rows1_no_div   + rows2_no_div   + rows3_no_div   + rows4_no_div  )
rows_only_div.extend(rows0_only_div + rows1_only_div + rows2_only_div + rows3_only_div + rows4_only_div)

# Now, Sort the rows using the sss_value and ssse_value formulas: [1:] skips the 1st title row
sorted_list_db               = sorted(csv_db_data,   key=lambda row:          row[0],           reverse=False)  # Sort by ticker symbol
sorted_list_sss              = sorted(rows,          key=lambda row:          row[3],           reverse=False)  # Sort by sss_value     -> The lower  - the more attractive
sorted_list_ssss             = sorted(rows,          key=lambda row:          row[4],           reverse=False)  # Sort by ssss_value    -> The lower  - the more attractive
sorted_list_sssss            = sorted(rows,          key=lambda row:          row[5],           reverse=False)  # Sort by sssss_value   -> The lower  - the more attractive
sorted_list_ssse             = sorted(rows,          key=lambda row:          row[6],           reverse=True )  # Sort by ssse_value    -> The higher - the more attractive
sorted_list_sssse            = sorted(rows,          key=lambda row:          row[7],           reverse=True )  # Sort by sssse_value   -> The higher - the more attractive
sorted_list_ssssse           = sorted(rows,          key=lambda row:          row[8],           reverse=True )  # Sort by ssssse_value  -> The higher - the more attractive
sorted_list_sss_no_div       = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[3],    reverse=False)  # Sort by sss_value     -> The lower  - the more attractive
sorted_list_ssss_no_div      = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[4],    reverse=False)  # Sort by ssss_value    -> The lower  - the more attractive
sorted_list_sssss_no_div     = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[5],    reverse=False)  # Sort by sssss_value   -> The lower  - the more attractive
sorted_list_ssse_no_div      = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[6],    reverse=True )  # Sort by ssse_value    -> The higher - the more attractive
sorted_list_sssse_no_div     = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[7],    reverse=True )  # Sort by sssse_value   -> The higher - the more attractive
sorted_list_ssssse_no_div    = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[8],    reverse=True )  # Sort by ssssse_value  -> The higher - the more attractive
sorted_list_sss_only_div     = sorted(rows_only_div, key=lambda row_only_div: row_only_div[3],  reverse=False)  # Sort by sss_value     -> The lower  - the more attractive
sorted_list_ssss_only_div    = sorted(rows_only_div, key=lambda row_only_div: row_only_div[4],  reverse=False)  # Sort by ssss_value    -> The lower  - the more attractive
sorted_list_sssss_only_div   = sorted(rows_only_div, key=lambda row_only_div: row_only_div[5],  reverse=False)  # Sort by sssss_value   -> The lower  - the more attractive
sorted_list_ssse_only_div    = sorted(rows_only_div, key=lambda row_only_div: row_only_div[6],  reverse=True )  # Sort by ssse_value    -> The higher - the more attractive
sorted_list_sssse_only_div   = sorted(rows_only_div, key=lambda row_only_div: row_only_div[7],  reverse=True )  # Sort by sssse_value   -> The higher - the more attractive
sorted_list_ssssse_only_div  = sorted(rows_only_div, key=lambda row_only_div: row_only_div[8],  reverse=True )  # Sort by ssssse_value  -> The higher - the more attractive
sorted_list_sssi             = sorted(rows,          key=lambda row:          row[9],           reverse=False)  # Sort by sssi_value    -> The lower  - the more attractive
sorted_list_ssssi            = sorted(rows,          key=lambda row:          row[10],          reverse=False)  # Sort by ssssi_value   -> The lower  - the more attractive
sorted_list_sssssi           = sorted(rows,          key=lambda row:          row[11],          reverse=False)  # Sort by sssssi_value  -> The lower  - the more attractive
sorted_list_sssei            = sorted(rows,          key=lambda row:          row[12],          reverse=True )  # Sort by sssei_value   -> The higher - the more attractive
sorted_list_ssssei           = sorted(rows,          key=lambda row:          row[13],          reverse=True )  # Sort by ssssei_value  -> The higher - the more attractive
sorted_list_sssssei          = sorted(rows,          key=lambda row:          row[14],          reverse=True )  # Sort by sssssei_value -> The higher - the more attractive
sorted_list_sssi_no_div      = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[9],    reverse=False)  # Sort by sssi_value    -> The lower  - the more attractive
sorted_list_ssssi_no_div     = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[10],   reverse=False)  # Sort by ssssi_value   -> The lower  - the more attractive
sorted_list_sssssi_no_div    = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[11],   reverse=False)  # Sort by sssssi_value  -> The lower  - the more attractive
sorted_list_sssei_no_div     = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[12],   reverse=True )  # Sort by sssei_value   -> The higher - the more attractive
sorted_list_ssssei_no_div    = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[13],   reverse=True )  # Sort by ssssei_value  -> The higher - the more attractive
sorted_list_sssssei_no_div   = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[14],   reverse=True )  # Sort by sssssei_value -> The higher - the more attractive
sorted_list_sssi_only_div    = sorted(rows_only_div, key=lambda row_only_div: row_only_div[9],  reverse=False)  # Sort by sssi_value    -> The lower  - the more attractive
sorted_list_ssssi_only_div   = sorted(rows_only_div, key=lambda row_only_div: row_only_div[10], reverse=False)  # Sort by ssssi_value   -> The lower  - the more attractive
sorted_list_sssssi_only_div  = sorted(rows_only_div, key=lambda row_only_div: row_only_div[11], reverse=False)  # Sort by sssssi_value  -> The lower  - the more attractive
sorted_list_sssei_only_div   = sorted(rows_only_div, key=lambda row_only_div: row_only_div[12], reverse=True )  # Sort by sssei_value   -> The higher - the more attractive
sorted_list_ssssei_only_div  = sorted(rows_only_div, key=lambda row_only_div: row_only_div[13], reverse=True )  # Sort by ssssei_value  -> The higher - the more attractive
sorted_list_sssssei_only_div = sorted(rows_only_div, key=lambda row_only_div: row_only_div[14], reverse=True )  # Sort by sssssei_value -> The higher - the more attractive

list_sss_best = []
list_sss_best.extend(sorted_list_sss             [:BEST_N_SELECT])
list_sss_best.extend(sorted_list_ssss            [:BEST_N_SELECT])
list_sss_best.extend(sorted_list_sssss           [:BEST_N_SELECT])
list_sss_best.extend(sorted_list_ssse            [:BEST_N_SELECT])
list_sss_best.extend(sorted_list_sssse           [:BEST_N_SELECT])
list_sss_best.extend(sorted_list_ssssse          [:BEST_N_SELECT])
list_sss_best.extend(sorted_list_sssi            [:BEST_N_SELECT])
list_sss_best.extend(sorted_list_ssssi           [:BEST_N_SELECT])
list_sss_best.extend(sorted_list_sssssi          [:BEST_N_SELECT])
list_sss_best.extend(sorted_list_sssei           [:BEST_N_SELECT])
list_sss_best.extend(sorted_list_ssssei          [:BEST_N_SELECT])
list_sss_best.extend(sorted_list_sssssei         [:BEST_N_SELECT])
sorted_list_sssss_best_with_duplicates = sorted(list_sss_best, key=lambda row: row[5], reverse=False)  # Sort by sssss_value   -> The lower  - the more attractive
sorted_list_sssss_best = list(k for k, _ in itertools.groupby(sorted_list_sssss_best_with_duplicates))

list_sss_best_no_div = []
list_sss_best_no_div.extend(sorted_list_sss_no_div    [:BEST_N_SELECT])
list_sss_best_no_div.extend(sorted_list_ssss_no_div   [:BEST_N_SELECT])
list_sss_best_no_div.extend(sorted_list_sssss_no_div  [:BEST_N_SELECT])
list_sss_best_no_div.extend(sorted_list_ssse_no_div   [:BEST_N_SELECT])
list_sss_best_no_div.extend(sorted_list_sssse_no_div  [:BEST_N_SELECT])
list_sss_best_no_div.extend(sorted_list_ssssse_no_div [:BEST_N_SELECT])
list_sss_best_no_div.extend(sorted_list_sssi_no_div   [:BEST_N_SELECT])
list_sss_best_no_div.extend(sorted_list_ssssi_no_div  [:BEST_N_SELECT])
list_sss_best_no_div.extend(sorted_list_sssssi_no_div [:BEST_N_SELECT])
list_sss_best_no_div.extend(sorted_list_sssei_no_div  [:BEST_N_SELECT])
list_sss_best_no_div.extend(sorted_list_ssssei_no_div [:BEST_N_SELECT])
list_sss_best_no_div.extend(sorted_list_sssssei_no_div[:BEST_N_SELECT])
sorted_list_sssss_best_no_div_with_duplicates = sorted(list_sss_best_no_div, key=lambda row: row[5], reverse=False)  # Sort by sssss_value   -> The lower  - the more attractive
sorted_list_sssss_best_no_div = list(k for k, _ in itertools.groupby(sorted_list_sssss_best_no_div_with_duplicates))

list_sss_best_only_div = []
list_sss_best_only_div.extend(sorted_list_sss_only_div    [:BEST_N_SELECT])
list_sss_best_only_div.extend(sorted_list_ssss_only_div   [:BEST_N_SELECT])
list_sss_best_only_div.extend(sorted_list_sssss_only_div  [:BEST_N_SELECT])
list_sss_best_only_div.extend(sorted_list_ssse_only_div   [:BEST_N_SELECT])
list_sss_best_only_div.extend(sorted_list_sssse_only_div  [:BEST_N_SELECT])
list_sss_best_only_div.extend(sorted_list_ssssse_only_div [:BEST_N_SELECT])
list_sss_best_only_div.extend(sorted_list_sssi_only_div   [:BEST_N_SELECT])
list_sss_best_only_div.extend(sorted_list_ssssi_only_div  [:BEST_N_SELECT])
list_sss_best_only_div.extend(sorted_list_sssssi_only_div [:BEST_N_SELECT])
list_sss_best_only_div.extend(sorted_list_sssei_only_div  [:BEST_N_SELECT])
list_sss_best_only_div.extend(sorted_list_ssssei_only_div [:BEST_N_SELECT])
list_sss_best_only_div.extend(sorted_list_sssssei_only_div[:BEST_N_SELECT])
sorted_list_sssss_best_only_div_with_duplicates = sorted(list_sss_best_only_div, key=lambda row: row[5], reverse=False)  # Sort by sssss_value   -> The lower  - the more attractive
sorted_list_sssss_best_only_div = list(k for k, _ in itertools.groupby(sorted_list_sssss_best_only_div_with_duplicates))

header_row = ["Ticker", "Name", "Sector", "sss_value", "ssss_value", "sssss_value", "ssse_value", "sssse_value", "ssssse_value", "sssi_value", "ssssi_value", "sssssi_value", "sssei_value", "ssssei_value", "sssssei_value", "enterprise_value_to_revenue", "trailing_price_to_earnings", "enterprise_value_to_ebitda", "profit_margin", "held_percent_institutions", "forward_eps", "trailing_eps", "price_to_book", "shares_outstanding", "net_income_to_common_shareholders", "nitcsh_to_shares_outstanding", "employees", "enterprise_value", "nitcsh_to_num_employees", "earnings_quarterly_growth", "price_to_earnings_to_growth_ratio", "last_dividend_0", "last_dividend_1", "last_dividend_2", "last_dividend_3" ]

sorted_lists_list = [
    sorted_list_db,
    sorted_list_sss,                        sorted_list_ssss,                       sorted_list_sssss,                      sorted_list_ssse,
    sorted_list_sssse,                      sorted_list_ssssse,                     sorted_list_sss_no_div,                 sorted_list_ssss_no_div,
    sorted_list_sssss_no_div,               sorted_list_ssse_no_div,                sorted_list_sssse_no_div,               sorted_list_ssssse_no_div,
    sorted_list_sss_only_div,               sorted_list_ssss_only_div,              sorted_list_sssss_only_div,             sorted_list_ssse_only_div,
    sorted_list_sssse_only_div,             sorted_list_ssssse_only_div,            sorted_list_sssi,                       sorted_list_ssssi,
    sorted_list_sssssi,                     sorted_list_sssei,                      sorted_list_ssssei,                     sorted_list_sssssei,
    sorted_list_sssi_no_div,                sorted_list_ssssi_no_div,               sorted_list_sssssi_no_div,              sorted_list_sssei_no_div,
    sorted_list_ssssei_no_div,              sorted_list_sssssei_no_div,             sorted_list_sssi_only_div,              sorted_list_ssssi_only_div,
    sorted_list_sssssi_only_div,            sorted_list_sssei_only_div,             sorted_list_ssssei_only_div,            sorted_list_sssssei_only_div,
    sorted_list_sssss_best,                 sorted_list_sssss_best_no_div,          sorted_list_sssss_best_only_div
]

for sorted_list in sorted_lists_list:
    sorted_list.insert(0, header_row)

tase_str    = ""
sectors_str = ""
all_str     = ""
csv_db_str  = ""
if TASE_MODE:                 tase_str    = "_TASE"
if len(SECTORS_LIST):         sectors_str = '_'+'_'.join(SECTORS_LIST)
if READ_UNITED_STATES_INPUT_SYMBOLS: all_str     = '_OTHERS'
if BUILD_CSV_DB == 0:         csv_db_str  = '_DB_REUSED'
date_and_time = time.strftime("Results/%Y%m%d-%H%M%S{}{}{}{}".format(tase_str, sectors_str, all_str, csv_db_str))

filenames_list = sss_filenames.create_filenames_list(date_and_time)

for index in range(len(filenames_list)):
    os.makedirs(os.path.dirname(filenames_list[index]), exist_ok=True)
    with open(filenames_list[index], mode='w', newline='') as engine:
        writer = csv.writer(engine)
        writer.writerows(sorted_lists_list[index])
