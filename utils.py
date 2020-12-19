import dash_html_components as html
import dash_core_components as dcc
import pandas_datareader.data as pdr
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pandas.api.types import CategoricalDtype
import dash_bootstrap_components as dbc
from datetime import date
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

class Stock:

	def __init__(self, ticker, start_date, end_date):

		self.ticker = ticker
		self.fin_data = self.get_fin_data(start_date, end_date)
		self.fin_data_by_day = self.analyse_by_weekday()

		self.avg_return = self.fin_data.d_returns.mean().round(2)
		self.avg_risk = self.fin_data.d_returns.std().round(2)

		self.period_return = self.get_period_return().round(2)
		self.green_pct = round(self.green_red_analyze(), 2)

		self.weekday_recommend = self.fin_data_by_day.idxmax()['d_returns']

	def get_fin_data(self, start_date, end_date, full_data=None):
		"""Basic raw financial data for a defined ticker
		:param start_date: Start of Finance Period
		:type start_date: datetime.datetime

		"""
		if full_data is None:
			stock = pdr.DataReader(self.ticker, 'yahoo', start_date, end_date)[['Adj Close', 'Volume']].round(2)
			stock['weekday'] = stock.index.day_name()
			cats = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
			cat_type = CategoricalDtype(categories=cats, ordered=True)
			stock['weekday'] = stock['weekday'].astype(cat_type)
			stock['d_returns'] = stock['Adj Close'].pct_change().mul(100).round(2)
			stock['gain'] = stock['d_returns'].loc[stock['d_returns'] >= 0]
			stock['loss'] = stock['d_returns'].loc[stock['d_returns'] < 0]
			return stock
		else:
			stock = pdr.DataReader(self.ticker, 'yahoo', start_date, end_date).round(2)
			stock['weekday'] = stock.index.day_name()
			stock['d_returns'] = stock['Adj Close'].pct_change().mul(100).round(2)
			cats = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
			cat_type = CategoricalDtype(categories=cats, ordered=True)
			stock['weekday'] = stock['weekday'].astype(cat_type)
			stock['d_returns'] = stock['Adj Close'].pct_change().mul(100).round(2)
			return stock

	def green_red_analyze(self):
		greens = self.fin_data.gain.count()
		to = self.fin_data.d_returns.count()
		green_pct = (greens/to) * 100
		return green_pct

	def analyse_by_weekday(self, gain_loss_split=True):
		if gain_loss_split is not None:
			sd = self.fin_data.groupby(['weekday']).count()
			sd['gain%'] = sd['gain'].div(sd['d_returns']).mul(100).round(2)
		return sd

	def plot_prices(self, graph_type='line'):
		if graph_type == 'line':
			stock_fig = px.line(self.fin_data, x=self.fin_data.index, y=self.fin_data['Adj Close'])
			return stock_fig

	def plot_return(self, graph_type='line'):
		if graph_type == 'line':
			stock_fig2 = px.line(self.fin_data, x=self.fin_data.index, y=self.fin_data['d_returns'])
			return stock_fig2

	def plot_weekly_distribution(self):
		sd = self.fin_data.groupby(['weekday']).mean()
		stock_fig2 = px.histogram(sd, x=sd.index, y=sd['d_returns'])
		return stock_fig2

	def plot_return_distribution(self):
		data = [go.Histogram(x=self.fin_data.d_returns, name=self.ticker)]
		fig = go.Figure(data)
		return fig

	def get_period_return(self):
		old_price = self.fin_data['Adj Close'].iloc[0]
		new_price = self.fin_data['Adj Close'].iloc[-1]

		x = ((new_price/old_price) - 1) * 100

		return x

	def get_summary(self):
		headers = {
			'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2_1 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Mobile/7B405'}
		x = f'https://finance.yahoo.com/quote/{self.ticker}/profile?p={self.ticker}'

		y = requests.get(x, headers=headers).text

		soup = BeautifulSoup(y, 'html.parser')

		yy = soup.find_all(class_='quote-sub-section')

		zz = yy[0].text

		zz_ = str(zz).replace("Description", "")

		return zz_

	def get_earnings_date(self):
		url1 = f"https://www.investing.com/search/?q={self.ticker}"
		initial = requests.get(url1, headers={'User-Agent': 'Mozilla/5.0'}).text
		b = BeautifulSoup(initial, 'html.parser').find("div", {
			"class": "js-inner-all-results-quotes-wrapper newResultsContainer quatesTable"})
		piece = b.find('a').get('href')
		url2 = f"https://www.investing.com{piece}-earnings"
		subsequent = requests.get(url2, headers={'User-Agent': 'Mozilla/5.0'}).content
		b2 = BeautifulSoup(subsequent, 'html.parser').find_all('tr', {'name': 'instrumentEarningsHistory'})
		for item in b2:
			return item.get('event_timestamp')

	def get_market_cap(self):
		url1 = f"https://www.investing.com/search/?q={self.ticker}"
		initial = requests.get(url1, headers={'User-Agent': 'Mozilla/5.0'}).text
		b = BeautifulSoup(initial, 'html.parser').find("div", {
			"class": "js-inner-all-results-quotes-wrapper newResultsContainer quatesTable"})
		piece = b.find('a').get('href')
		url2 = f"https://www.investing.com{piece}"
		subsequent = requests.get(url2, headers={'User-Agent': 'Mozilla/5.0'}).content
		b2 = BeautifulSoup(subsequent, 'html.parser').find_all('div', {'class': 'clear overviewDataTable overviewDataTableWithTooltip'})
		x = list([item.text for item in b2])
		y = str(x)[92:95]
		print(y)
		y = str(x)[95:100]
		print(y)

	def plot_initial_investment(self, capital=10000):
		cumulative_returns = self.fin_data['d_returns'].div(100) + 1
		self.fin_data['investment'] = cumulative_returns.cumprod()
		self.fin_data['investment'] = self.fin_data['investment'].mul(capital).round(2)
		investment_figure = px.line(self.fin_data, x=self.fin_data.index, y=self.fin_data['investment'])
		self.investment_fv = "{:,}".format(self.fin_data.investment.iloc[-1])
		return investment_figure

	def get_company_overview(self):
		#API
		fun='OVERVIEW'
		symbol = self.ticker
		api = "WC0M5MFIXOZTY0QD"
		url = f'https://www.alphavantage.co/query?function={fun}&symbol={symbol}&apikey={api}'
		response = requests.get(url).json()

		# Market Info
		self.description = response['Description']
		self.sector = response['Sector']
		self.market_cap = int(response['MarketCapitalization']) / 1000000000
		try:
			self.pe_ratio = float(response['PERatio'])
		except:
			self.pe_ratio = response['PERatio']

		try:
			self.ebitda = int(response['EBITDA']) / 1000000
		except:
			self.ebitda = response['PERatio']

		try:
			self.ev_to_ebitda = float(response['EVToEBITDA'])
		except:
			self.ev_to_ebitda = response['EVToEBITDA']

		try:
			self.institutional_investors = float(response['PercentInstitutions'])
		except:
			self.institutional_investors = response['PercentInstitutions']

		try:
			self.insider_investors = float(response['PercentInsiders'])

		except:
			self.insider_investors = response['PercentInsiders']

		try:
			self.beta = float(response['Beta'])
		except:
			self.beta = response['Beta']

		try:
			data = [self.sector, f'{round(self.market_cap, 2)} B', f'{round(self.institutional_investors, 2)} %', f'{round(self.insider_investors, 2)} %', round(self.beta,2), round(self.ev_to_ebitda, 2), round(self.pe_ratio, 2), self.get_earnings_date()]
		except:
			data = [self.sector, f'{round(self.market_cap, 2)} B', f'{self.institutional_investors} %',
					f'{self.insider_investors} %', self.beta, self.ev_to_ebitda,
					self.pe_ratio, self.get_earnings_date()]

		index = ['Sector', 'Market Capitalization','Institutional Ownership', 'Insider Ownership','Beta','Enterprise Value-To-EBITDA','Price-To-Earnings (PE)', 'Next Earnings Date']

		df = pd.DataFrame(data, index=index, columns=['Data'])
		df.reset_index(inplace=True)

		# summary = pd.Series({
		# 	'Sector':self.sector,
		# 	'Market Capitalization': f'{round(self.market_cap, 2)} B',
		# 	'Institutional Ownership': f'{round(self.institutional_investors, 2)} %',
		# 	'Insider Ownership': f'{round(self.insider_investors, 2)} %',
		# 	'Beta': round(self.beta,2),
		# 	'Enterprise Value-To-EBITDA': round(self.ev_to_ebitda, 2),
		# 	'Price-To-Earnings (PE)': round(self.pe_ratio, 2),
		# 	'Next Earnings Date': self.get_earnings_date(),
		# })
		return df

	def price_performance_summary(self):
		three_month_start = date.today() - relativedelta(months=+3)
		six_month_start = date.today() - relativedelta(months=+6)
		three_months = Stock(self.ticker, start_date=three_month_start, end_date=date.today())
		six_months = Stock(self.ticker, start_date=six_month_start, end_date=date.today())


		summary = {
			'Selected Period':['Selected Period',self.period_return,self.avg_return, self.avg_risk, self.green_pct, 'TBD', self.weekday_recommend],
			'Past 3 months':["Past 3 months",three_months.period_return, three_months.avg_return, three_months.avg_risk, three_months.green_pct, 'TBD', three_months.weekday_recommend],
			'Past 6 months':["Past 6 months",six_months.period_return, six_months.avg_return, six_months.avg_risk, six_months.green_pct, 'TBD', six_months.weekday_recommend],
		}
		i = ["Metrics","Period Return (%)", "Avg Return (%)", "Volatility (%)", "Green Days (%)", "Outperforming Strategy", "Most Likely Green Weekday"]

		df = pd.DataFrame(summary, index=i)
		df.reset_index(inplace=True)
		return df


def Header(app):
    return html.Div([get_header(app), html.Br([]), get_menu()])

controls = html.Div([
    dcc.Input(id='ticker', placeholder='Ticker', style={'margin-left':'10px', 'width':'75px', 'font-size':'10px'}, persistence=True),
    dcc.DatePickerRange(id='time-horizon', initial_visible_month=date(2020, 1, 1), display_format='DD MMM YY',persistence=True, calendar_orientation='vertical', style={'font-size':'10px'}),
    html.Button('Submit', id='submit-val', style={'float':'right'})
], id='content')

def get_header(app):
    header = html.Div(
        [
            html.Div(
                [
                    html.A(
						html.Img(
							src=app.get_asset_url("r2.png"),
							className="logo", style={'width': '300px', 'height': '100px'}
						), href="/price-performance"
					),
                    html.A(
                        html.H6("by RS", id="learn-more-button"),
                        href="",
                        # TODO: Add my LinkedIn Profile Link
                    ),
                ],
                className="row",
            ),
            html.Div(
                [
                    html.Div(
                        [html.H5("Financial Dashboard")],
                        className="seven columns main-title",
                    ),
                ],
                className="twelve columns",
                style={"padding-left": "0"},
            ),
        ],
        className="row",
    )
    return header


def get_menu():
    menu = html.Div(
        [
			dcc.Link(
				"Overview",
				href="/overview",
				className="tab first",
			),
            dcc.Link(
                "Price Performance",
                href="/price-performance",
                className="tab",
            ),
			dcc.Link(
				"Market Overview",
				href="/market",
				className="tab"
			),
			dcc.Link(
                "Trends & Predictions",
                href="/trends",
                className="tab",
            ),
            dcc.Link(
                "Social Media Sentiment", href="/social-media", className="tab"
            ),
        ],
        className="row all-tabs",
    )
    return menu

def make_dash_table(df):
    """ Return a dash definition of an HTML table for a Pandas dataframe """
    table = []
    for index, row in df.iterrows():
        html_row = []
        for i in range(len(row)):
            html_row.append(html.Td([row[i]]))
        table.append(html.Tr(html_row))
    return table

def get_stocks(market_cap, sector, sortable):
	import requests as r
	import pandas as pd
	url = f"https://finviz.com/screener.ashx?v=111&f=cap_{market_cap},geo_usa,sec_{sector}&o=-{sortable}"
	g = r.get(url, headers={'User-Agent': 'Mozilla/5.0'})
	df = pd.read_html(g.text)[-2]
	header = df.iloc[0]
	df.rename(columns=header, inplace=True)
	df.drop(labels=["No.", "Country", "P/E"], axis=1, inplace=True)
	return df

def blank_overview():
	data = ["N/A", "N/A", "N/A","N/A", "N/A","N/A", "N/A", "N/A"]
	index = ['Sector', 'Market Capitalization', 'Institutional Ownership', 'Insider Ownership', 'Beta',
			 'Enterprise Value-To-EBITDA', 'Price-To-Earnings (PE)', 'Next Earnings Date']

	df = pd.DataFrame(data, index=index, columns=['Data'])
	df.reset_index(inplace=True)
	return df

def blank_price_summary():
	summary = {
		'Selected Period': ['Selected Period', "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
		'Past 3 months': ["Past 3 months", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
		'Past 6 months': ["Past 6 months", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
	}
	i = ["Metrics", "Period Return (%)", "Avg Return (%)", "Volatility (%)", "Green Days (%)", "Outperforming Strategy",
		 "Most Likely Green Weekday"]

	df = pd.DataFrame(summary, index=i)
	df.reset_index(inplace=True)
	return df