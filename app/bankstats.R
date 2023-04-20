library(rvest) 
library(tidyverse)
library(tsibble)
library(readxl)
library(jsonlite)
library(here)

prepare_backseries <- function() { 
    colnames <- readxl::read_excel(
        path=here('Data', 'APRA Reporting Institute Names by Sector.xlsx'), 
        sheet="ColNames")
    categories <- readxl::read_excel(
        path=here('Data', 'APRA Reporting Institute Names by Sector.xlsx'))
    # backseries 
    url <- here("Data", "back_series.xlsx")
    data.backseries <- readxl::read_excel(url, sheet="Table 1", 
                       col_names=colnames$New, 
                       skip=1) %>% 
        rename("Institution"="Institution Name") %>% 
        select(-starts_with("Drop")) %>% 
        mutate(
            `Total deposits` = `Intra-group deposits` + `Total residents deposits` + `Cash and deposits with financial institutions`, 
            `Total borrowings` = `Total short-term borrowings` + `Total long-term borrowings` + `Negotiable Certificates of Deposit`, 
            `Total funding` = `Total deposits` + `Total borrowings`,
            `Total loans` = `Total residents loans and finance leases` + 
                `Intra-group loans and finance leases`, 
            `Total housing loans` = `Loans to households: Housing: Owner-occupied` + 
                `Loans to households: Housing: Investment`) %>% 
        pivot_longer(cols=-c("Period", "ABN", "Institution"), 
                     names_to="Measure", 
                     values_to="ValueMillion") %>% 
        inner_join(categories %>% select(Institute_Name, Sector, Sector2), 
                   by=c("Institution"="Institute_Name")) %>% 
        mutate(Period = tsibble::yearmonth(Period), 
               ABN = format(ABN, big.mark = " ")) 
    return(data.backseries) } 

download_banking_stats <- function() {  
    categories <- readxl::read_excel('Data/APRA Reporting Institute Names by Sector.xlsx')
    url <- "https://www.apra.gov.au/monthly-authorised-deposit-taking-institution-statistics"
    site <- read_html(url) 
    path <- site %>% html_elements(".document-link") %>% html_attr("href")  
    download.file(url=path[2], here("Data", "temp.xlsx")) 
    readxl::read_excel(path=here("Data", "temp.xlsx"), 
                       sheet = "Table 1", 
                       skip=1) %>% 
        rename("Institution"="Institution Name") %>% 
        mutate(
            `Total deposits` = `Intra-group deposits` + `Total residents deposits` + `Cash and deposits with financial institutions`, 
            `Total borrowings` = `Total short-term borrowings` + `Total long-term borrowings` + `Negotiable Certificates of Deposit`, 
            `Total funding` = `Total deposits` + `Total borrowings`,
            `Total loans` = `Total residents loans and finance leases` + 
                `Intra-group loans and finance leases`, 
            `Total housing loans` = `Loans to households: Housing: Owner-occupied` + 
                `Loans to households: Housing: Investment`) %>% 
        pivot_longer(cols=-c("Period", "ABN", "Institution"), 
                     names_to="Measure", 
                     values_to="ValueMillion") %>% 
        inner_join(categories %>% select(Institute_Name, Sector, Sector2), 
                  by=c("Institution"="Institute_Name")) %>% 
        mutate(Period = tsibble::yearmonth(Period), 
               ABN = format(ABN, big.mark = " "))  } 

summarise_top_banks <- function(data, topn=6, topby="Total residents assets") { 
    sector_top_banks <- data %>% 
        filter(Measure==topby) %>% 
        filter(Period==max(Period)) %>% 
        group_by(Sector) %>% 
        top_n(n=topn, wt=ValueMillion) %>% 
        pull("Institution")
    data %>% 
        mutate(InstitutionSumm=ifelse(Institution %in% sector_top_banks, Institution, paste("Other", Sector))) %>% 
        group_by(Period, Measure, Sector, InstitutionSumm) %>% 
        summarise(ValueMillion=sum(ValueMillion))
    }

ggplot_bank_trends <- function(data, sector=NULL, measure=NULL) { 
    if (is.null(measure)) { measure <- data$Measure[1] }
    if (is.null(sector)) { sector <- "BIG 4" } 
    add_average <- TRUE
    data.temp <- data %>% 
        filter(Sector == sector) %>% 
        filter(Measure == measure) 
    if (length(unique(data.temp$Institution))>6) { 
        topn <- data.temp %>% 
            filter(Period==max(Period)) %>% 
            top_n(n=6, wt=ValueMillion) %>% 
            pull("Institution")
        data.temp <- data.temp %>% 
            mutate(Institution=ifelse(Institution %in% topn, Institution, "All others")) %>% 
            group_by(Period, Institution) %>% 
            summarise(ValueMillion = sum(ValueMillion))  
        add_average <- FALSE
    }
    p1 <- data.temp %>% 
        ggplot(aes(x=Period, y=ValueMillion, col=Institution)) + 
        geom_line() + 
        theme_bw() + 
        scale_y_log10(labels=scales::comma) + 
        theme(legend.position = "bottom", 
              legend.direction = "vertical") + 
        labs(col=NULL, x=NULL, y = "AUD Milliion", 
             title=paste("Trend", measure, "by Institution"), 
             subtitle="APRA Monthly Banking Statistics")
    if (add_average==TRUE) { 
        p1 <- p1 + 
            stat_summary(inherit.aes=FALSE, 
                         mapping=aes(x=Period, y=ValueMillion, linetype="Average"), 
                         fun="mean", geom="line") + 
            labs(linetype=NULL) } 
    return(p1) }

ggplot_sector_trends <- function(data, measure=NULL) { 
    if (is.null(measure)) { measure <- data$Measure[1] }
    key_sectors <- c("BIG 4", "Mutuals/Customer Owned", "2nd Tier Banks")
    data %>% 
        filter(Measure == measure) %>% 
        mutate(Sector = ifelse(Sector %in% key_sectors, Sector, "Other")) %>% 
        group_by(Period, Sector) %>% 
        summarise(ValueMillion=sum(ValueMillion)) %>% 
        ggplot(aes(x=Period, y=ValueMillion, col=Sector)) + 
        geom_line() + 
        theme_bw() 
}

# ----- Run -----
data.backseries <- prepare_backseries()
write_rds(data.backseries, here("Data", "bank_stats_backseries.rds"))

# Regular Run ----- 
data <- download_banking_stats() 
data.backseries <-  read_rds(here("Data", "bank_stats_backseries.rds")) %>% 
    filter(!(Period %in% data$Period)) 
data.summ <- bind_rows(data, data.backseries) %>% 
    summarise_top_banks() 

#save out ... 
write_rds(data.summ, here("Data", "banking_stats.rds"))
write_json(data.summ %>% mutate(Period=as.Date(Period)), 
     here("app", "banking_stats.json"), 
     auto_unbox = TRUE)


