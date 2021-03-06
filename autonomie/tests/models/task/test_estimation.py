# -*- coding: utf-8 -*-
# * Authors:
#       * TJEBBES Gaston <g.t@majerti.fr>
#       * Arezki Feth <f.a@majerti.fr>;
#       * Miotte Julien <j.m@majerti.fr>;
import datetime


def test_estimation_set_numbers(full_estimation):
    full_estimation.date = datetime.date(1969, 7, 1)
    full_estimation.set_numbers(5, 18)
    assert full_estimation.internal_number == u"Company 1969-07 D5"
    assert full_estimation.name == u"Devis 18"
    assert full_estimation.project_index == 18


def test_duplicate_estimation(dbsession, full_estimation):
    newestimation = full_estimation.duplicate(
        full_estimation.owner,
        project=full_estimation.project,
        phase=full_estimation.phase,
        customer=full_estimation.customer,
    )
    for key in "customer", "address", "expenses_ht", "workplace":
        assert getattr(newestimation, key) == getattr(full_estimation, key)
    assert newestimation.status == 'draft'
    assert newestimation.project == full_estimation.project
    assert newestimation.status_person == full_estimation.owner
    assert newestimation.internal_number.startswith("Company {0:%Y-%m}".format(
        datetime.date.today()
    ))
    assert newestimation.phase == full_estimation.phase
    assert newestimation.mentions == full_estimation.mentions
    assert len(full_estimation.default_line_group.lines) == len(
        newestimation.default_line_group.lines
    )
    assert len(full_estimation.payment_lines) == len(
        newestimation.payment_lines
    )
    assert len(full_estimation.discounts) == len(newestimation.discounts)


def test_light_gen_invoice(dbsession, full_estimation):
    from autonomie.models.task import Invoice
    invoices = full_estimation.gen_invoices(full_estimation.owner)
    for inv in invoices:
        dbsession.add(inv)
        dbsession.flush()

    invoices = Invoice.query().filter(
        Invoice.estimation_id == full_estimation.id
    ).all()
    assert len(invoices) == 3

    deposit = invoices[0]
    assert deposit.date == datetime.date.today()
    assert deposit.address == full_estimation.address
    assert deposit.workplace == full_estimation.workplace
    assert deposit.financial_year == datetime.date.today().year
    assert deposit.total() == full_estimation.deposit_amount_ttc()
    assert deposit.mentions == full_estimation.mentions

    total = sum([i.total() for i in invoices])
    assert total == full_estimation.total()

def test_gen_invoice_ref450(dbsession, full_estimation):
    # for line in full_estimation.all_lines:
        # line.product_id = None

    invoices = full_estimation.gen_invoices(full_estimation.owner)
    for invoice in invoices:
        for line in invoice.all_lines:
            assert line.product_id is not None


def test_duplicate_payment_line(payment_line):
    newline = payment_line.duplicate()
    for i in ('order', 'description', 'amount'):
        assert getattr(newline, i) == getattr(payment_line, i)

    today = datetime.date.today()
    assert newline.date == today
