<html>
<head>
    <style type="text/css">
        body {
            background: #fff;
            margin: 0;
            padding: 0;
        }

        .center {
            text-align: center;
        }

        .right {
            text-align: right;
        }

        .top {
             vertical-align: top;
        }

        .bottom {
             vertical-align: bottom;
        }

        .p6 {
            font-size: 6pt;
        }

        .p8 {
            font-size: 8pt;
        }

        .p14 {
            font-size: 8pt;
        }

        .bold {
            font-weight: bold;
        }

        table {
            border: 1px solid black;
            width: 100%;
            border-collapse: collapse;
            border-spacing: 0;
            empty-cells: show;

        }

        table thead td {
            text-align: center;
            vertical-align: top;
        }

        table td {
            border: 1px solid black;
        }

        table.header {
            border: none;
        }

        table.header td {
            border: none;
            border-bottom: 1px solid black;
        }

        table.footer {
            border: none;
        }

        table.footer td {
            border: none;
        }
    </style>

</head>
% for o in objects:
<body>
    <div class="right p6">Приложение N 1<br>
к постановлению Правительства<br>
Российской Федерации<br>
от 26 декабря 2011 г. № 1137
    </div>
    <table class="p8 header">
        <tr>
            <td class="p10 bold">Счет-фактура № ${ o.id or '-'} от ${ get_date(o.document_date) or '-' }</td>
            <td class="right">(1)</td>
        </tr>
        <tr>
            <td class="p10 bold">Исправление № -----от-----</td>
            <td class="right">(1а)</td>
        </tr>
        <tr>
            <td>Продавец: ${ o.invoice_id.account_id.full or '-' }</td>
            <td class="right">(2)</td>
        </tr>
        <tr>
            <td>Адрес: ${ o.invoice_id.account_id.address or '-' }</td>
            <td class="right">(2а)</td>
        </tr>
        <tr>
            <td>ИНН/КПП продавца: ${ o.invoice_id.account_id.inn  or '-'}/${ o.invoice_id.account_id.kpp or '-' }</td>
            <td class="right">(2б)</td>
        </tr>
        <tr>
            <td>Грузоотправитель и его адрес: --</td>
            <td class="right">(3)</td>
        </tr>
        <tr>
            <td>Грузополучатель и его адрес: --</td>
            <td class="right">(4)</td>
        </tr>
        <tr>
            <td>К платежно-расчетному документу:
                % for p in o.invoice_id.pay_ids:
                    ${ p.getter }
                    % if not loop.last:
                        ${', '}
                    % endif
                % endfor
            </td>
            <td class="right">(5)</td>
        </tr>
        <tr>
            <td>Покупатель: ${ o.invoice_id.bank_id.fullname or '-' }</td>
            <td class="right">(6)</td>
        </tr>
        <tr>
            <td>Адрес: ${ get_client_address(o.invoice_id.bank_id.id) or '-'}</td>
            <td class="right">(6а)</td>
        </tr>
        <tr>
            <td>ИНН/КПП покупателя: ${ o.invoice_id.bank_id.inn or '-' }/${ o.invoice_id.bank_id.kpp or '-' }</td>
            <td class="right">(6б)</td>
        </tr>
        <tr>
            <td>Валюта: наименование, код Российский рубль, 643</td>
            <td class="right">(7)</td>
        </tr>
    </table>
    <br />
    <table class="p8" style="word-wrap: break-word;">
        <thead>
        <tr>
            <td rowspan="2">Наименование товара (описание выполненных работ, оказанных услуг) имущественного права</td>
            <td colspan="2">Единица измерения</td>
            <td rowspan="2" width="35">Количество (объем)</td>
            <td rowspan="2" width="80">Цена<br> (тариф)<br> за<br> единицу<br> измерения</td>
            <td rowspan="2" width="85">Стоимость<br> товаров (работ, услуг),<br> имущественных прав без налога - всего</td>
            <td rowspan="2" width="60">В том<br> числе<br> сумма<br> акциза</td>
            <td rowspan="2" width="75">Налоговая<br> ставка</td>
            <td rowspan="2" width="75">Сумма<br> налога,<br> предъявляемая<br> покупателю</td>
            <td rowspan="2" width="85">Стоимость<br> товаров (работ, услуг),<br> имущественных прав с налога - всего</td>
            <td colspan="2">Страна происхождения</td>
            <td rowspan="2" width="80">Номер<br> таможенной<br> декларации</td>
        </tr>
        <tr>
            <td width="40">Код</td>
            <td width="90">Условное<br> обозначение<br> (национальное)</td>
            <td width="45">Цифровой<br> код</td>
            <td width="100">Краткое<br> наименование</td>
        </tr>
        <tr>
            <td>1</td>
            <td>2</td>
            <td>2а</td>
            <td>3</td>
            <td>4</td>
            <td>5</td>
            <td>6</td>
            <td>7</td>
            <td>8</td>
            <td>9</td>
            <td>10</td>
            <td>10а</td>
            <td>11</td>
        </tr>
        </thead>
        <tfoot>
        <tr>
            <td colspan="5"></td>
            <td class="right">${ get_total(o.document_cash, o.invoice_id.tax)[0] }</td>
            <td colspan="2" class="center">Х</td>
            <td class="right">${ get_total(o.document_cash, o.invoice_id.tax)[1] }</td>
            <td class="right">${ o.document_cash }</td>
        </tr>
        </tfoot>
        % for l in o.document_line_id:
            <tr>
                <td>${ l.service_id.name }</td>
                <td>796</td>
                <td class="right">шт.</td>
                <td class="right">1</td>
                <td class="right">${ get_total(l.name, o.invoice_id.tax)[0] }</td>
                <td class="right">${ get_total(l.name, o.invoice_id.tax)[0] }</td>
                <td>Без акциз</td>
                <td class="right">${ o.invoice_id.tax } %</td>
                <td class="right">${ get_total(l.name, o.invoice_id.tax)[1] }</td>
                <td class="right">${ l.name }</td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
        % endfor
    </table>
    <br>
    <table class="footer p8">
        <tr>
            <td rowspan="2" class="right">Руководитель организации<br> или иное<br> уполномоченное лицо</td>
            <td colspan="2" class="right" style="border-bottom: 1px solid black; width: 300px;">${ o.invoice_id.account_id.responsible }</td>
            <td rowspan="2" class="right">Главный бухгалтер или<br> иное уполномоченное<br> лицо</td>
            <td colspan="2" class="right" style="border-bottom: 1px solid black;">${ o.invoice_id.account_id.responsible }</td>
        </tr>
        <tr class="top center">
            <td>(подпись)</td>
            <td>(ф.и.о.)</td>
            <td>(подпись)</td>
            <td>(ф.и.о.)</td>
        </tr>
        <tr>
            <td rowspan="2" class="right">Индивидуальный предприниматель</td>
            <td colspan="5" class="right" style="border-bottom: 1px solid black;">&nbsp;</td>
        </tr>
        <tr class="top center">
            <td>(подпись)</td>
            <td>(ф.и.о.)</td>
            <td colspan="3">(реквизиты свидетельства о государственной регистрации индивидуального предпринимателя)</td>
        </tr>
    </table>
    <p class="p6">Примечание 1. Первый экземпляр счет-фактуры, составленного на бумажном носителе - полкупателю, второй экземпляр - продавцу. 2. При составлении организацией счета-фактуры в электронном виде показатель "Главный бухгалтер (подпись) (ФИО)"
 не формируется.</p>
</body>
% endfor
</html>