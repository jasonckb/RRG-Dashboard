def create_rrg_chart(data, benchmark, sectors, sector_names, universe, timeframe):
    if timeframe == "Weekly":
        data_resampled = data.resample('W-FRI').last()
    else:  # Daily
        data_resampled = data

    rrg_data = pd.DataFrame()
    for sector in sectors:
        rs_ratio, rs_momentum = calculate_rrg_values(data_resampled[sector], data_resampled[benchmark])
        rrg_data[f"{sector}_RS-Ratio"] = rs_ratio
        rrg_data[f"{sector}_RS-Momentum"] = rs_momentum

    # Use only the last 5 data points (current + 4 historical)
    last_n_periods = rrg_data.iloc[-5:]

    # Calculate the min and max values with padding
    padding = 0.05  # 5% padding
    min_x = last_n_periods[[f"{sector}_RS-Ratio" for sector in sectors]].min().min()
    max_x = last_n_periods[[f"{sector}_RS-Ratio" for sector in sectors]].max().max()
    min_y = last_n_periods[[f"{sector}_RS-Momentum" for sector in sectors]].min().min()
    max_y = last_n_periods[[f"{sector}_RS-Momentum" for sector in sectors]].max().max()

    range_x = max_x - min_x
    range_y = max_y - min_y
    min_x = max(min_x - range_x * padding, 90)  # Ensure minimum is not less than 90
    max_x = min(max_x + range_x * padding, 110)  # Ensure maximum is not more than 110
    min_y = max(min_y - range_y * padding, 90)
    max_y = min(max_y + range_y * padding, 110)

    fig = go.Figure()

    quadrant_colors = {"Lagging": "pink", "Weakening": "lightyellow", "Improving": "lightblue", "Leading": "lightgreen"}
    curve_colors = {"Lagging": "red", "Weakening": "orange", "Improving": "darkblue", "Leading": "darkgreen"}

    def get_quadrant(x, y):
        if x < 100 and y < 100: return "Lagging"
        elif x >= 100 and y < 100: return "Weakening"
        elif x < 100 and y >= 100: return "Improving"
        else: return "Leading"

    for sector in sectors:
        x_values = last_n_periods[f"{sector}_RS-Ratio"].dropna()
        y_values = last_n_periods[f"{sector}_RS-Momentum"].dropna()
        if len(x_values) > 0 and len(y_values) > 0:
            current_quadrant = get_quadrant(x_values.iloc[-1], y_values.iloc[-1])
            color = curve_colors[current_quadrant]
            
            # Modify the legend label and chart label based on the universe
            if universe == "US Sectors":
                legend_label = sector
                chart_label = sector
            elif universe == "HK Sub-indexes":
                legend_label = sector
                chart_label = sector.replace('.HK', '')  # Remove .HK suffix
            else:
                legend_label = f"{sector} ({sector_names[sector]})"
                chart_label = f"{sector_names[sector]}"
            
            # Prepare hover data
            hover_text = [
                f"Ticker: {sector}<br>" +
                f"Name: {sector_names[sector]}<br>" +
                f"Date: {data_resampled.index[i].strftime('%Y-%m-%d')}<br>" +
                f"RS-Ratio: {x:.2f}<br>" +
                f"RS-Momentum: {y:.2f}<br>" +
                f"Close Price: ${data_resampled[sector].iloc[i]:.2f}<br>" +
                f"Quadrant: {get_quadrant(x, y)}"
                for i, (x, y) in enumerate(zip(x_values, y_values))
            ]

            fig.add_trace(go.Scatter(
                x=x_values, y=y_values, mode='lines+markers', name=legend_label,
                line=dict(color=color, width=2), marker=dict(size=6, symbol='circle'),
                legendgroup=sector, showlegend=True,
                hoverinfo='text',
                hovertext=hover_text,
                hoverlabel=dict(bgcolor="white", font_size=12, font_family="Rockwell")
            ))
            
            # Determine if current momentum is higher or lower than previous
            momentum_change = y_values.iloc[-1] - y_values.iloc[-2] if len(y_values) > 1 else 0
            text_position = "top center" if momentum_change >= 0 else "bottom center"
            
            fig.add_trace(go.Scatter(
                x=[x_values.iloc[-1]], y=[y_values.iloc[-1]], mode='markers+text',
                name=f"{sector} (latest)", marker=dict(color=color, size=12, symbol='circle'),
                text=[chart_label], textposition=text_position, legendgroup=sector, showlegend=False,
                textfont=dict(color='black', size=12, family='Arial Black'),
                hoverinfo='text',
                hovertext=hover_text[-1],
                hoverlabel=dict(bgcolor="white", font_size=12, font_family="Rockwell")
            ))

    fig.update_layout(
        title=f"Relative Rotation Graph (RRG) for {'S&P 500' if universe == 'US' else 'Hang Seng' if universe == 'HK' else 'World'} {'Sectors' if universe != 'WORLD' else 'Indices'} ({timeframe})",
        xaxis_title="RS-Ratio",
        yaxis_title="RS-Momentum",
        width=1200,
        height=800,
        xaxis=dict(range=[min_x, max_x], title_font=dict(size=14)),
        yaxis=dict(range=[min_y, max_y], title_font=dict(size=14)),
        plot_bgcolor='white',
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.02, title=f"Legend<br>Benchmark: {'ACWI (MSCI World)' if universe == 'WORLD' else benchmark}"),
        hovermode='closest',
        shapes=[
            dict(type="rect", xref="x", yref="y", x0=min_x, y0=100, x1=100, y1=max_y, fillcolor="lightblue", opacity=0.5, line_width=0),
            dict(type="rect", xref="x", yref="y", x0=100, y0=100, x1=max_x, y1=max_y, fillcolor="lightgreen", opacity=0.5, line_width=0),
            dict(type="rect", xref="x", yref="y", x0=min_x, y0=min_y, x1=100, y1=100, fillcolor="pink", opacity=0.5, line_width=0),
            dict(type="rect", xref="x", yref="y", x0=100, y0=min_y, x1=max_x, y1=100, fillcolor="lightyellow", opacity=0.5, line_width=0),
            dict(type="line", xref="x", yref="y", x0=100, y0=min_y, x1=100, y1=max_y, line=dict(color="black", width=1)),
            dict(type="line", xref="x", yref="y", x0=min_x, y0=100, x1=max_x, y1=100, line=dict(color="black", width=1)),
        ]
    )

    # Adjust quadrant label positions to corners
    label_font = dict(size=32, color='black', family='Arial Black')
    fig.add_annotation(x=min_x, y=min_y, text="落後", showarrow=False, font=label_font, xanchor="left", yanchor="bottom")
    fig.add_annotation(x=max_x, y=min_y, text="轉弱", showarrow=False, font=label_font, xanchor="right", yanchor="bottom")
    fig.add_annotation(x=min_x, y=max_y, text="改善", showarrow=False, font=label_font, xanchor="left", yanchor="top")
    fig.add_annotation(x=max_x, y=max_y, text="領先", showarrow=False, font=label_font, xanchor="right", yanchor="top")

    return fig
